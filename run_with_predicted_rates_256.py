from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import argparse
import os, math
import json
import glob
import random
import collections
import math
import time
import pdb

from subprocess import check_output

parser = argparse.ArgumentParser()

""" Cannot use gpu frac, because E[GPU proc. percentile]~=1 """
# Assume that you have 12GB of GPU memory and want to allocate ~4GB:
# gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.333)
# sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))

parser.add_argument("--input_dir", help="path to folder containing images")
parser.add_argument("--mode", required=True, choices=["train", "test", "export"])
parser.add_argument("--output_dir", required=True, help="where to put output files")
parser.add_argument("--seed", type=int)
parser.add_argument("--rps_size", type=int)
parser.add_argument("--checkpoint", default=None, help="directory with checkpoint to resume training from or use for testing")

parser.add_argument("--max_steps", type=int, help="number of training steps (0 to disable)")
parser.add_argument("--max_epochs", type=int, help="number of training epochs")
parser.add_argument("--summary_freq", type=int, default=100000, help="update summaries every summary_freq steps")
parser.add_argument("--progress_freq", type=int, default=5000, help="display progress every progress_freq steps")
parser.add_argument("--trace_freq", type=int, default=0, help="trace execution every trace_freq steps")
parser.add_argument("--display_freq", type=int, default=0, help="write current training images every display_freq steps")
# parser.add_argument("--save_freq", type=int, default=25000, help="save model every save_freq steps, 0 to disable")
parser.add_argument("--save_freq", type=int, default=100000, help="save model every save_freq steps, 0 to disable")

parser.add_argument("--label_length", type=int, default=10, help="write current training images every display_freq steps")
parser.add_argument("--separable_conv", action="store_true", help="use separable convolutions in the generator")
parser.add_argument("--aspect_ratio", type=float, default=1.0, help="aspect ratio of output images (width/height)")
parser.add_argument("--lab_colorization", action="store_true", help="split input image into brightness (A) and color (B)")
parser.add_argument("--batch_size", type=int, default=1, help="number of images in batch")
parser.add_argument("--which_direction", type=str, default="AtoB", choices=["AtoB", "BtoA","AtoA"])
parser.add_argument("--loss", type=str, default="adv-l1", choices=["ssim", "l1","adv-l1"])
parser.add_argument("--ngf", type=int, default=64, help="number of generator filters in first conv layer")
parser.add_argument("--ndf", type=int, default=64, help="number of discriminator filters in first conv layer")
parser.add_argument("--scale_size", type=int, default=286, help="scale images to this size before cropping to 256x256")
parser.add_argument("--flip", dest="flip", action="store_true", help="flip images horizontally")
parser.add_argument("--no_flip", dest="flip", action="store_false", help="don't flip images horizontally")
parser.set_defaults(flip=True)
parser.add_argument("--lr", type=float, default=0.0002, help="initial learning rate for adam")
parser.add_argument("--beta1", type=float, default=0.5, help="momentum term of adam")
parser.add_argument("--l1_weight", type=float, default=100.0, help="weight on L1 term for generator gradient")
parser.add_argument("--quality_weight", type=float, default=1.0, help="weight on quality term for generator gradient")
parser.add_argument("--gan_weight", type=float, default=1.0, help="weight on GAN term for generator gradient")
parser.add_argument("--gpu", help="GPU ID")

# Export options
parser.add_argument("--output_filetype", default="png", choices=["png", "jpeg"])
a = parser.parse_args()

# Select GPU
os.environ["CUDA_VISIBLE_DEVICES"]=a.gpu

# Macros
EPS = 1e-12
# CROP_SIZE = 256
RPS = a.rps_size

CROP_SIZE = 128*2
a.scale_size = CROP_SIZE

# a.aspect_ratio = float(1280)/720
a.aspect_ratio = 1.0

LABEL_DIGITS = a.label_length
# LABEL_DIGITS = 10

# Examples = collections.namedtuple("Examples", "labels, paths, inputs, targets, count, steps_per_epoch")
Examples = collections.namedtuple("Examples", "rp_inputs, rp_targets, labels, paths, inputs, targets, count, steps_per_epoch")
Model = collections.namedtuple("Model", "predicted_rate, ssim_io, ssim_it, rate_relative_error, rate_predictor_loss, predict_rate, outputs, predict_real, predict_fake, discrim_loss, discrim_grads_and_vars, gen_loss_GAN, gen_loss_L1, gen_loss_quality, gen_grads_and_vars, train")

# Imported helpers ...
# The following functions define frequently used layers
def preprocess(image):
    with tf.name_scope("preprocess"):
        # [0, 1] => [-1, 1]
        return image * 2 - 1


def deprocess(image):
    with tf.name_scope("deprocess"):
        # [-1, 1] => [0, 1]
        return (image + 1) / 2


def preprocess_lab(lab):
    with tf.name_scope("preprocess_lab"):
        L_chan, a_chan, b_chan = tf.unstack(lab, axis=2)
        # L_chan: black and white with input range [0, 100]
        # a_chan/b_chan: color channels with input range ~[-110, 110], not exact
        # [0, 100] => [-1, 1],  ~[-110, 110] => [-1, 1]
        return [L_chan / 50 - 1, a_chan / 110, b_chan / 110]


def deprocess_lab(L_chan, a_chan, b_chan):
    with tf.name_scope("deprocess_lab"):
        # this is axis=3 instead of axis=2 because we process individual images but deprocess batches
        return tf.stack([(L_chan + 1) / 2 * 100, a_chan * 110, b_chan * 110], axis=3)


def discrim_conv(batch_input, out_channels, stride):
    padded_input = tf.pad(batch_input, [[0, 0], [1, 1], [1, 1], [0, 0]], mode="CONSTANT")
    return tf.layers.conv2d(padded_input, out_channels, kernel_size=4, strides=(stride, stride), padding="valid", kernel_initializer=tf.random_normal_initializer(0, 0.02))


def gen_conv(batch_input, out_channels):
    # [batch, in_height, in_width, in_channels] => [batch, out_height, out_width, out_channels]
    initializer = tf.random_normal_initializer(0, 0.02)
    if a.separable_conv:
        return tf.layers.separable_conv2d(batch_input, out_channels, kernel_size=4, strides=(2, 2), padding="same", depthwise_initializer=initializer, pointwise_initializer=initializer)
    else:
        return tf.layers.conv2d(batch_input, out_channels, kernel_size=4, strides=(2, 2), padding="same", kernel_initializer=initializer)


def gen_deconv(batch_input, out_channels):
    # [batch, in_height, in_width, in_channels] => [batch, out_height, out_width, out_channels]
    initializer = tf.random_normal_initializer(0, 0.02)
    if a.separable_conv:
        _b, h, w, _c = batch_input.shape
        resized_input = tf.image.resize_images(batch_input, [h * 2, w * 2], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
        return tf.layers.separable_conv2d(resized_input, out_channels, kernel_size=4, strides=(1, 1), padding="same", depthwise_initializer=initializer, pointwise_initializer=initializer)
    else:
        return tf.layers.conv2d_transpose(batch_input, out_channels, kernel_size=4, strides=(2, 2), padding="same", kernel_initializer=initializer)


def lrelu(x, a):
    with tf.name_scope("lrelu"):
        # adding these together creates the leak part and linear part
        # then cancels them out by subtracting/adding an absolute value term
        # leak: a*x/2 - a*abs(x)/2
        # linear: x/2 + abs(x)/2

        # this block looks like it has 2 inputs on the graph unless we do this
        x = tf.identity(x)
        return (0.5 * (1 + a)) * x + (0.5 * (1 - a)) * tf.abs(x)


# Norm layer to correct variance shift ..
def batchnorm(inputs):
    return tf.layers.batch_normalization(inputs, axis=3, epsilon=1e-5, momentum=0.1, training=True, gamma_initializer=tf.random_normal_initializer(1.0, 0.02))


def check_image(image):
    assertion = tf.assert_equal(tf.shape(image)[-1], 3, message="image must have 3 color channels")
    with tf.control_dependencies([assertion]):
        image = tf.identity(image)

    if image.get_shape().ndims not in (3, 4):
        raise ValueError("image must be either 3 or 4 dimensions")

    # make the last dimension 3 so that you can unstack the colors
    shape = list(image.get_shape())
    shape[-1] = 3
    image.set_shape(shape)
    return image


def load_examples():
    if a.input_dir is None or not os.path.exists(a.input_dir):
        raise Exception("input_dir does not exist")

    input_paths = glob.glob(os.path.join(a.input_dir, "*.jpg"))
    decode = tf.image.decode_jpeg
    if len(input_paths) == 0:
        input_paths = glob.glob(os.path.join(a.input_dir, "*.png"))
        decode = tf.image.decode_png

    if len(input_paths) == 0:
        raise Exception("input_dir contains no image files")

    def get_name(path):
        name, _ = os.path.splitext(os.path.basename(path))
        return name

    # if the image names are numbers, sort by the value rather than asciibetically
    # having sorted inputs means that the outputs are sorted in test mode
    if all(get_name(path).isdigit() for path in input_paths):
        input_paths = sorted(input_paths, key=lambda path: int(get_name(path)))
    else:
        input_paths = sorted(input_paths)

    with tf.name_scope("load_images"):
        path_queue = tf.train.string_input_producer(input_paths, shuffle=a.mode == "train")
        reader = tf.WholeFileReader()
        paths, contents = reader.read(path_queue)
        raw_input = decode(contents)
        raw_input = tf.image.convert_image_dtype(raw_input, dtype=tf.float32)

        # Parse label ..
        # +1 to include / at the end
        suffix_length = len('/'.join(input_paths[0].split('/')[:-1])) + 1

        size_label_length = LABEL_DIGITS
        # Get bits allocated to frame from first <size_label_length> digits in filename
        labels = tf.string_to_number(tf.substr(paths,suffix_length,size_label_length),tf.float32)

        assertion = tf.assert_equal(tf.shape(raw_input)[2], 3, message="image does not have 3 channels")
        with tf.control_dependencies([assertion]):
            raw_input = tf.identity(raw_input)

        raw_input.set_shape([None, None, 3])


        # break apart image pair and move to range [-1, 1]
        width = tf.shape(raw_input)[1] # [height, width, channels]
        # define width of each tile in input tensor
        w = width//(2+RPS)
        # a_images = preprocess(raw_input[:,:w,:])
        # b_images = preprocess(raw_input[:,w:2*w,:])

        # load x and x_e ..
        input_frames = []
        for k in range(2+RPS):
           input_frames.append(preprocess(raw_input[:, k*w:(k+1)*w, :]))
        a_images = input_frames[0] ; b_images = input_frames[1]
        if RPS > 0:
           rps_images = input_frames[2:]
        else:
           rps_images = []
        # pdb.set_trace()
        # a_images = preprocess(raw_input[:,:width//2,:])
        # b_images = preprocess(raw_input[:,width//2:,:])

    if a.which_direction == "AtoB":
        inputs, targets = [a_images, b_images]
    elif a.which_direction == "BtoA":
        inputs, targets = [b_images, a_images]
    elif a.which_direction == 'AtoA':
        inputs, targets = [a_images, a_images]
    else:
        raise Exception("invalid direction")

    # synchronize seed for image operations so that we do the same operations to both
    # input and output images
    seed = random.randint(0, 2**31 - 1)
    def transform(image):
        r = image
        if a.flip:
            r = tf.image.random_flip_left_right(r, seed=seed)

        # area produces a nice downscaling, but does nearest neighbor for upscaling
        # assume we're going to be doing downscaling here

        # RESIZE for RESCALE
        # r = tf.image.resize_images(r, [a.scale_size, a.scale_size], method=tf.image.ResizeMethod.AREA)

        # CROP for RESCALE
        r = tf.image.crop_to_bounding_box(r, 0, 0, a.scale_size, a.scale_size)

        offset = tf.cast(tf.floor(tf.random_uniform([2], 0, a.scale_size - CROP_SIZE + 1, seed=seed)), dtype=tf.int32)
        if a.scale_size > CROP_SIZE:
            r = tf.image.crop_to_bounding_box(r, offset[0], offset[1], CROP_SIZE, CROP_SIZE)
        elif a.scale_size < CROP_SIZE:
            raise Exception("scale size cannot be less than crop size")
        return r

    def transform_resize(image):
        r = image
        if a.flip:
            r = tf.image.random_flip_left_right(r, seed=seed)

        # area produces a nice downscaling, but does nearest neighbor for upscaling
        # assume we're going to be doing downscaling here

        # RESIZE for RESCALE
        r = tf.image.resize_images(r, [a.scale_size, a.scale_size], method=tf.image.ResizeMethod.AREA)

        # CROP for RESCALE
        # r = tf.image.crop_to_bounding_box(r, 0, 0, a.scale_size, a.scale_size)

        offset = tf.cast(tf.floor(tf.random_uniform([2], 0, a.scale_size - CROP_SIZE + 1, seed=seed)), dtype=tf.int32)
        if a.scale_size > CROP_SIZE:
            r = tf.image.crop_to_bounding_box(r, offset[0], offset[1], CROP_SIZE, CROP_SIZE)
        elif a.scale_size < CROP_SIZE:
            raise Exception("scale size cannot be less than crop size")
        return r


    with tf.name_scope("input_images"):
        input_images = transform(inputs)

    with tf.name_scope("target_images"):
        target_images = transform(targets)

    with tf.name_scope("rp_input_images"):
        rp_input_images = transform_resize(inputs)

    with tf.name_scope("rp_target_images"):
        rp_target_images = transform_resize(targets)






    # labels_batch, paths_batch, inputs_batch, targets_batch = tf.train.batch([labels, paths, input_images, target_images], batch_size=a.batch_size)
    labels_batch, paths_batch, inputs_batch, targets_batch, rp_inputs_batch, rp_targets_batch = tf.train.batch([labels, paths, input_images, target_images, rp_input_images, rp_target_images], batch_size=a.batch_size)
    steps_per_epoch = int(math.ceil(len(input_paths) / a.batch_size))

    return Examples(
        rp_inputs=rp_inputs_batch,
        rp_targets=rp_targets_batch,
        labels=labels_batch,
        paths=paths_batch,
        inputs=inputs_batch,
        targets=targets_batch,
        count=len(input_paths),
        steps_per_epoch=steps_per_epoch
    )

def create_generator(generator_inputs, generator_outputs_channels):
    layers = []

    # encoder_1: [batch, 256, 256, in_channels] => [batch, 128, 128, ngf]
    with tf.variable_scope("encoder_1"):
        output = gen_conv(generator_inputs, a.ngf)
        layers.append(output)

    layer_specs = [
        a.ngf * 2, # encoder_2: [batch, 128, 128, ngf] => [batch, 64, 64, ngf * 2]
        a.ngf * 4, # encoder_3: [batch, 64, 64, ngf * 2] => [batch, 32, 32, ngf * 4]
        a.ngf * 8, # encoder_4: [batch, 32, 32, ngf * 4] => [batch, 16, 16, ngf * 8]
        a.ngf * 8, # encoder_5: [batch, 16, 16, ngf * 8] => [batch, 8, 8, ngf * 8]
        a.ngf * 8, # encoder_6: [batch, 8, 8, ngf * 8] => [batch, 4, 4, ngf * 8]
        a.ngf * 8, # encoder_7: [batch, 4, 4, ngf * 8] => [batch, 2, 2, ngf * 8]
        a.ngf * 8, # encoder_8: [batch, 2, 2, ngf * 8] => [batch, 1, 1, ngf * 8]
    ]

    for out_channels in layer_specs:
        with tf.variable_scope("encoder_%d" % (len(layers) + 1)):
            rectified = lrelu(layers[-1], 0.2)
            # [batch, in_height, in_width, in_channels] => [batch, in_height/2, in_width/2, out_channels]
            convolved = gen_conv(rectified, out_channels)
            output = batchnorm(convolved)
            layers.append(output)

    layer_specs = [
        (a.ngf * 8, 0.5),   # decoder_8: [batch, 1, 1, ngf * 8] => [batch, 2, 2, ngf * 8 * 2]
        (a.ngf * 8, 0.5),   # decoder_7: [batch, 2, 2, ngf * 8 * 2] => [batch, 4, 4, ngf * 8 * 2]
        (a.ngf * 8, 0.5),   # decoder_6: [batch, 4, 4, ngf * 8 * 2] => [batch, 8, 8, ngf * 8 * 2]
        (a.ngf * 8, 0.0),   # decoder_5: [batch, 8, 8, ngf * 8 * 2] => [batch, 16, 16, ngf * 8 * 2]
        (a.ngf * 4, 0.0),   # decoder_4: [batch, 16, 16, ngf * 8 * 2] => [batch, 32, 32, ngf * 4 * 2]
        (a.ngf * 2, 0.0),   # decoder_3: [batch, 32, 32, ngf * 4 * 2] => [batch, 64, 64, ngf * 2 * 2]
        (a.ngf, 0.0),       # decoder_2: [batch, 64, 64, ngf * 2 * 2] => [batch, 128, 128, ngf * 2]
    ]

    num_encoder_layers = len(layers)
    for decoder_layer, (out_channels, dropout) in enumerate(layer_specs):
        skip_layer = num_encoder_layers - decoder_layer - 1
        with tf.variable_scope("decoder_%d" % (skip_layer + 1)):
            if decoder_layer == 0:
                # first decoder layer doesn't have skip connections
                # since it is directly connected to the skip_layer
                input = layers[-1]
            else:
                input = tf.concat([layers[-1], layers[skip_layer]], axis=3)

            rectified = tf.nn.relu(input)
            # [batch, in_height, in_width, in_channels] => [batch, in_height*2, in_width*2, out_channels]
            output = gen_deconv(rectified, out_channels)
            output = batchnorm(output)

            if dropout > 0.0:
                output = tf.nn.dropout(output, keep_prob=1 - dropout)

            layers.append(output)

    # decoder_1: [batch, 128, 128, ngf * 2] => [batch, 256, 256, generator_outputs_channels]
    with tf.variable_scope("decoder_1"):
        input = tf.concat([layers[-1], layers[0]], axis=3)
        rectified = tf.nn.relu(input)
        output = gen_deconv(rectified, generator_outputs_channels)
        output = tf.tanh(output)
        layers.append(output)

    return layers[-1]


def create_model(inputs, targets, rate_labels, rp_inputs, rp_targets):

    def create_rate_predictor(discrim_inputs, discrim_targets):
        n_layers = 3
        layers = []

        # 2x [batch, height, width, in_channels] => [batch, height, width, in_channels * 2]
        input = tf.concat([discrim_inputs, discrim_targets], axis=3)
        # pdb.set_trace()

        # layer_1: [batch, 256, 256, in_channels * 2] => [batch, 128, 128, ndf]
        with tf.variable_scope("layer_1"):
            convolved = discrim_conv(input, a.ndf, stride=2)
            rectified = lrelu(convolved, 0.2)
            layers.append(rectified)

        # layer_2: [batch, 128, 128, ndf] => [batch, 64, 64, ndf * 2]
        # layer_3: [batch, 64, 64, ndf * 2] => [batch, 32, 32, ndf * 4]
        # layer_4: [batch, 32, 32, ndf * 4] => [batch, 31, 31, ndf * 8]
        for i in range(n_layers):
            with tf.variable_scope("layer_%d" % (len(layers) + 1)):
                out_channels = a.ndf * min(2**(i+1), 8)
                stride = 1 if i == n_layers - 1 else 2  # last layer here has stride 1
                convolved = discrim_conv(layers[-1], out_channels, stride=stride)
                normalized = batchnorm(convolved)
                rectified = lrelu(normalized, 0.2)
                layers.append(rectified)

        # layer_5: [batch, 31, 31, ndf * 8] => [batch, 30, 30, 1]
        with tf.variable_scope("layer_%d" % (len(layers) + 1)):
            convolved = discrim_conv(rectified, out_channels=1, stride=1)
            # pdb.set_trace()
            # output = tf.contrib.layers.fully_connected(inputs=convolved, num_outputs=1)
            output = tf.reshape(tf.contrib.layers.fully_connected(inputs=tf.layers.flatten(convolved), num_outputs=1), ())
            # output = tf.sigmoid(convolved)
            layers.append(output)

        return layers[-1]





    def create_discriminator(discrim_inputs, discrim_targets):
        n_layers = 3
        layers = []

        # 2x [batch, height, width, in_channels] => [batch, height, width, in_channels * 2]
        input = tf.concat([discrim_inputs, discrim_targets], axis=3)

        # layer_1: [batch, 256, 256, in_channels * 2] => [batch, 128, 128, ndf]
        with tf.variable_scope("layer_1"):
            convolved = discrim_conv(input, a.ndf, stride=2)
            rectified = lrelu(convolved, 0.2)
            layers.append(rectified)

        # layer_2: [batch, 128, 128, ndf] => [batch, 64, 64, ndf * 2]
        # layer_3: [batch, 64, 64, ndf * 2] => [batch, 32, 32, ndf * 4]
        # layer_4: [batch, 32, 32, ndf * 4] => [batch, 31, 31, ndf * 8]
        for i in range(n_layers):
            with tf.variable_scope("layer_%d" % (len(layers) + 1)):
                out_channels = a.ndf * min(2**(i+1), 8)
                stride = 1 if i == n_layers - 1 else 2  # last layer here has stride 1
                convolved = discrim_conv(layers[-1], out_channels, stride=stride)
                normalized = batchnorm(convolved)
                rectified = lrelu(normalized, 0.2)
                layers.append(rectified)

        # layer_5: [batch, 31, 31, ndf * 8] => [batch, 30, 30, 1]
        with tf.variable_scope("layer_%d" % (len(layers) + 1)):
            convolved = discrim_conv(rectified, out_channels=1, stride=1)
            output = tf.sigmoid(convolved)
            layers.append(output)

        return layers[-1]

    with tf.variable_scope("generator"):
        out_channels = int(targets.get_shape()[-1])
        outputs = create_generator(inputs, out_channels)

    # create two copies of discriminator, one for real pairs and one for fake pairs
    # they share the same underlying variables
    with tf.name_scope("real_discriminator"):
        with tf.variable_scope("discriminator"):
            # 2x [batch, height, width, channels] => [batch, 30, 30, 1]
            predict_real = create_discriminator(inputs, targets)

    with tf.name_scope("fake_discriminator"):
        with tf.variable_scope("discriminator", reuse=True):
            # 2x [batch, height, width, channels] => [batch, 30, 30, 1]
            predict_fake = create_discriminator(inputs, outputs)

    with tf.name_scope("discriminator_loss"):
        # minimizing -tf.log will try to get inputs to 1
        # predict_real => 1
        # predict_fake => 0
        discrim_loss = tf.reduce_mean(-(tf.log(predict_real + EPS) + tf.log(1 - predict_fake + EPS)))

    with tf.name_scope("rate_predictor"):
        with tf.variable_scope("predictor"):
            # 2x [batch, height, width, channels] => [batch, 30, 30, 1]
            # predict_rate = create_rate_predictor(inputs, targets)
            predict_rate = create_rate_predictor(rp_inputs, rp_targets)

    with tf.name_scope("rate_predictor_loss"):
        rate_predictor_loss = tf.square(tf.reduce_mean(predict_rate) - tf.cast(rate_labels, tf.float32))
        rate_relative_error = tf.abs((tf.reduce_mean(predict_rate) - tf.cast(rate_labels, tf.float32)))/tf.cast(rate_labels, tf.float32)
        # pdb.set_trace()

        rate_predictor_loss = tf.reshape(rate_predictor_loss, shape=())
        rate_relative_error = tf.reshape(rate_relative_error, shape=())

        predicted_rate = predict_rate

    with tf.name_scope("generator_loss"):
        # predict_fake => 1
        # abs(targets - outputs) => 0
        gen_loss_GAN = tf.reduce_mean(-tf.log(predict_fake + EPS))
        gen_loss_L1 = tf.reduce_mean(tf.abs(targets - outputs))

        # pdb.set_trace()
        max_val = 1
        # ssim is directly correlated with quality of reconstruction, therefor (l=1/ssim OR l=log*(ssim))
        # gen_loss_quality = tf.reshape(tf.log(tf.image.ssim(targets, outputs, max_val)), ())

        rectified_ssim = tf.reduce_max(tf.stack([tf.reshape(tf.image.ssim(targets, outputs, max_val),()),tf.constant(float(EPS))],axis=0))
        normalized_ssim =  tf.reshape((tf.image.ssim(targets, outputs, max_val) + 1)/2, ())
        gen_loss_quality = tf.log(1/rectified_ssim)
        # pdb.set_trace()
        ssim_it =  tf.reshape(tf.image.ssim(inputs, targets, max_val), shape=())
        ssim_io =  tf.reshape(tf.image.ssim(inputs, outputs, max_val), shape=())

        # gen_loss_quality = tf.reshape(tf.reduce_max(tf.concat(1/tf.image.ssim(targets, outputs, max_val), tf.constant(EPS))),())


        # gen_loss = gen_loss_GAN * a.gan_weight + gen_loss_L1 * a.l1_weight + gen_loss_quality * a.quality_weight
        # gen_loss = gen_loss_GAN * a.gan_weight + gen_loss_quality * a.quality_weight

        if a.loss == 'l1':
           gen_loss = gen_loss_L1 * a.l1_weight
        elif a.loss == 'ssim':
           gen_loss = gen_loss_quality * a.l1_weight
        else:
           gen_loss = gen_loss_GAN * a.gan_weight + gen_loss_L1 * a.l1_weight

    with tf.name_scope("discriminator_train"):
        discrim_tvars = [var for var in tf.trainable_variables() if var.name.startswith("discriminator")]
        discrim_optim = tf.train.AdamOptimizer(a.lr, a.beta1)
        discrim_grads_and_vars = discrim_optim.compute_gradients(discrim_loss, var_list=discrim_tvars)
        discrim_train = discrim_optim.apply_gradients(discrim_grads_and_vars)

    with tf.name_scope("generator_train"):
        with tf.control_dependencies([discrim_train]):
            gen_tvars = [var for var in tf.trainable_variables() if var.name.startswith("generator")]
            gen_optim = tf.train.AdamOptimizer(a.lr, a.beta1)
            gen_grads_and_vars = gen_optim.compute_gradients(gen_loss, var_list=gen_tvars)
            gen_train = gen_optim.apply_gradients(gen_grads_and_vars)

    with tf.name_scope("rate_predictor_train"):
        # with tf.control_dependencies([discrim_train]):
        p_tvars = [var for var in tf.trainable_variables() if var.name.startswith("predictor")]
        p_optim = tf.train.AdamOptimizer(a.lr, a.beta1)
        p_grads_and_vars = p_optim.compute_gradients(rate_predictor_loss, var_list=p_tvars)
        # pdb.set_trace()
        p_train = p_optim.apply_gradients(p_grads_and_vars)



    ema = tf.train.ExponentialMovingAverage(decay=0.99)
    update_losses = ema.apply([discrim_loss, gen_loss_GAN, gen_loss_L1,  gen_loss_quality, rate_predictor_loss])
    # update_losses = ema.apply([discrim_loss, gen_loss_GAN, gen_loss_L1, gen_loss_quality, rate_predictor_loss])
    # update_losses = ema.apply([discrim_loss, gen_loss_GAN, gen_loss_L1])

    global_step = tf.train.get_or_create_global_step()
    incr_global_step = tf.assign(global_step, global_step+1)

    return Model(
        predicted_rate=predicted_rate,
        ssim_io=ssim_io,
        ssim_it=ssim_it,
        predict_rate=predict_rate,
        rate_predictor_loss=ema.average(rate_predictor_loss),
        rate_relative_error=rate_relative_error,
        predict_real=predict_real,
        predict_fake=predict_fake,
        discrim_loss=ema.average(discrim_loss),
        discrim_grads_and_vars=discrim_grads_and_vars,
        gen_loss_GAN=ema.average(gen_loss_GAN),
        gen_loss_L1=ema.average(gen_loss_L1),
        gen_loss_quality=ema.average(gen_loss_quality),
        gen_grads_and_vars=gen_grads_and_vars,
        outputs=outputs,
        train=tf.group(update_losses, incr_global_step, gen_train, p_train),
    )


def save_images(fetches, step=None):
    image_dir = os.path.join(a.output_dir, "images")
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    filesets = []
    for i, in_path in enumerate(fetches["paths"]):
        name, _ = os.path.splitext(os.path.basename(in_path.decode("utf8")))
        fileset = {"name": name, "step": step}
        for kind in ["inputs", "outputs", "targets"]:
            filename = name + "-" + kind + ".png"
            if step is not None:
                filename = "%08d-%s" % (step, filename)
            fileset[kind] = filename
            out_path = os.path.join(image_dir, filename)
            contents = fetches[kind][i]
        #    with open(out_path, "wb") as f: //commented jubran
        #        f.write(contents) //commented jubran
        filesets.append(fileset)
    return filesets


def append_index(filesets, step=False):
    index_path = os.path.join(a.output_dir, "index.html")
    if os.path.exists(index_path):
        index = open(index_path, "a")
    else:
        index = open(index_path, "w")
        index.write("<html><body><table><tr>")
        if step:
            index.write("<th>step</th>")
        index.write("<th>name</th><th>input</th><th>output</th><th>target</th></tr>")

    for fileset in filesets:
        index.write("<tr>")

        if step:
            index.write("<td>%d</td>" % fileset["step"])
        index.write("<td>%s</td>" % fileset["name"])

        for kind in ["inputs", "outputs", "targets"]:
            index.write("<td><img src='images/%s'></td>" % fileset[kind])

        index.write("</tr>")
    return index_path


def main():
    if a.seed is None:
        a.seed = random.randint(0, 2**31 - 1)

    tf.set_random_seed(a.seed)
    np.random.seed(a.seed)
    random.seed(a.seed)

    if not os.path.exists(a.output_dir):
        os.makedirs(a.output_dir)

    if a.mode == "test" or a.mode == "export":
        if a.checkpoint is None:
            raise Exception("checkpoint required for test mode")

        # load some options from the checkpoint
        options = {"which_direction", "ngf", "ndf", "lab_colorization"}
        with open(os.path.join(a.checkpoint, "options.json")) as f:
            for key, val in json.loads(f.read()).items():
                if key in options:
                    print("loaded", key, "=", val)
                    setattr(a, key, val)
        # disable these features in test mode
        a.scale_size = CROP_SIZE
        a.flip = False

    for k, v in a._get_kwargs():
        print(k, "=", v)

    with open(os.path.join(a.output_dir, "options.json"), "w") as f:
        f.write(json.dumps(vars(a), sort_keys=True, indent=4))

    if a.mode == "export":


        # input = tf.placeholder(tf.string, shape=[1])
        # input_data = tf.decode_base64(input[0])

        # input = tf.placeholder(tf.string, shape=[])
        # input_data = input
        # # input_data = tf.decode_base64(input[0])

        # input_image = tf.image.decode_png(input_data)

        # # remove alpha channel if present
        # input_image = tf.cond(tf.equal(tf.shape(input_image)[2], 4), lambda: input_image[:,:,:3], lambda: input_image)
        # # convert grayscale to RGB
        # input_image = tf.cond(tf.equal(tf.shape(input_image)[2], 1), lambda: tf.image.grayscale_to_rgb(input_image), lambda: input_image)

        input = tf.placeholder(tf.float32, shape=[CROP_SIZE,CROP_SIZE,3])
        input_image = tf.image.convert_image_dtype(input, dtype=tf.float32)
        # input_image = tf.image.convert_image_dtype(input_image, dtype=tf.float32)
        input_image.set_shape([CROP_SIZE, CROP_SIZE, 3])
        batch_input = tf.expand_dims(input_image, axis=0)

        with tf.variable_scope("generator"):
            batch_output = deprocess(create_generator(preprocess(batch_input), 3))

        output_image = tf.image.convert_image_dtype(batch_output, dtype=tf.uint8)[0]
        if a.output_filetype == "png":
            output_data = tf.image.encode_png(output_image)
        elif a.output_filetype == "jpeg":
            output_data = tf.image.encode_jpeg(output_image, quality=80)
        else:
            raise Exception("invalid filetype")
        output = tf.convert_to_tensor([tf.encode_base64(output_data)])

        key = tf.placeholder(tf.string, shape=[1])
        inputs = {
            "key": key.name,
            "input": input.name
        }
        tf.add_to_collection("inputs", json.dumps(inputs))
        outputs = {
            "key":  tf.identity(key).name,
            "output": output.name,
        }
        tf.add_to_collection("outputs", json.dumps(outputs))
        tf.add_to_collection("rm_input", input)
        tf.add_to_collection("rm_output", output_image)
        # tf.add_to_collection("newoutput", output)

        init_op = tf.global_variables_initializer()
        restore_saver = tf.train.Saver()
        export_saver = tf.train.Saver()

        with tf.Session() as sess:
            sess.run(init_op)
            print("loading model from checkpoint")
            checkpoint = tf.train.latest_checkpoint(a.checkpoint)
            pdb.set_trace()
            restore_saver.restore(sess, checkpoint)
            print("exporting model")
            export_saver.export_meta_graph(filename=os.path.join(a.output_dir, "export.meta"))
            export_saver.save(sess, os.path.join(a.output_dir, "export"), write_meta_graph=False)

        return

    examples = load_examples()
    print("examples count = %d" % examples.count)

    # inputs and targets are [batch_size, height, width, channels]
    model = create_model(examples.inputs, examples.targets, examples.labels, examples.rp_inputs, examples.rp_targets)
    # model = create_model(examples.inputs, examples.targets)

    # undo colorization splitting on images that we use for display/output
    
    inputs = deprocess(examples.inputs)
    # pdb.set_trace()
    targets = deprocess(examples.targets)
    labels = deprocess(examples.labels)
    outputs = deprocess(model.outputs)

    def convert(image):
        if a.aspect_ratio != 1.0:
            # upscale to correct aspect ratio
            size = [CROP_SIZE, int(round(CROP_SIZE * a.aspect_ratio))]
            image = tf.image.resize_images(image, size=size, method=tf.image.ResizeMethod.BICUBIC)

        return tf.image.convert_image_dtype(image, dtype=tf.uint8, saturate=True)

    # reverse any processing on images so they can be written to disk or displayed to user
    with tf.name_scope("convert_inputs"):
        converted_inputs = convert(inputs)

    with tf.name_scope("convert_targets"):
        converted_targets = convert(targets)

    with tf.name_scope("convert_outputs"):
        converted_outputs = convert(outputs)

    with tf.name_scope("encode_images"):
        display_fetches = {
            "paths": examples.paths,
            "inputs": tf.map_fn(tf.image.encode_png, converted_inputs, dtype=tf.string, name="input_pngs"),
            "targets": tf.map_fn(tf.image.encode_png, converted_targets, dtype=tf.string, name="target_pngs"),
            "outputs": tf.map_fn(tf.image.encode_png, converted_outputs, dtype=tf.string, name="output_pngs"),
        }

    # summaries
    with tf.name_scope("inputs_summary"):
        tf.summary.image("inputs", converted_inputs)
        # to check min and max values of inputs ..
        tf.summary.histogram('converted_inputs' + "/values", converted_inputs)
        tf.summary.histogram('inputs' + "/values", inputs)
        tf.summary.histogram('labels' + "/values", labels)

    with tf.name_scope("targets_summary"):
        tf.summary.image("targets", converted_targets)

    with tf.name_scope("outputs_summary"):
        tf.summary.image("outputs", converted_outputs)

    with tf.name_scope("predict_real_summary"):
        tf.summary.image("predict_real", tf.image.convert_image_dtype(model.predict_real, dtype=tf.uint8))

    with tf.name_scope("predict_fake_summary"):
        tf.summary.image("predict_fake", tf.image.convert_image_dtype(model.predict_fake, dtype=tf.uint8))

    tf.summary.scalar("discriminator_loss", model.discrim_loss)
    tf.summary.scalar("generator_loss_GAN", model.gen_loss_GAN)
    tf.summary.scalar("generator_loss_L1", model.gen_loss_L1)
    tf.summary.scalar("rate_predictor_loss", model.rate_predictor_loss)
    tf.summary.scalar("rate_relative_error", model.rate_relative_error)
    tf.summary.scalar("rate_predictor_distance_from_target (kB)", tf.sqrt(model.rate_predictor_loss))

    max_val = 1
    ssim_image_input_target =  tf.reshape(tf.image.ssim(inputs, targets, max_val), shape=())
    ssim_image_input_output =  tf.reshape(tf.image.ssim(inputs, outputs, max_val), shape=())


    tf.summary.scalar("SSIM(Input, Target)", ssim_image_input_target)
    tf.summary.scalar("SSIM(Input, Output)", ssim_image_input_output)
    tf.summary.scalar("gen_loss_quality (SSIM)", model.gen_loss_quality)


    # pdb.set_trace()

    for var in tf.trainable_variables():
        tf.summary.histogram(var.op.name + "/values", var)

    for grad, var in model.discrim_grads_and_vars + model.gen_grads_and_vars:
        tf.summary.histogram(var.op.name + "/gradients", grad)

    with tf.name_scope("parameter_count"):
        parameter_count = tf.reduce_sum([tf.reduce_prod(tf.shape(v)) for v in tf.trainable_variables()])

    saver = tf.train.Saver(max_to_keep=1)

    logdir = a.output_dir if (a.trace_freq > 0 or a.summary_freq > 0) else None
    sv = tf.train.Supervisor(logdir=logdir, save_summaries_secs=0, saver=None)
    with sv.managed_session() as sess:
        print("parameter_count =", sess.run(parameter_count))

        if a.checkpoint is not None:
            print("loading model from checkpoint")
            checkpoint = tf.train.latest_checkpoint(a.checkpoint)
            saver.restore(sess, checkpoint)

        max_steps = 2**32
        if a.max_epochs is not None:
            max_steps = examples.steps_per_epoch * a.max_epochs
        if a.max_steps is not None:
            max_steps = a.max_steps

        if a.mode == "test":
            # # testing
            # # at most, process the test data once
            # start = time.time()
            # max_steps = min(examples.steps_per_epoch, max_steps)
            # for step in range(max_steps):
            #     results = sess.run(display_fetches)
            #     filesets = save_images(results)
            #     for i, f in enumerate(filesets):
            #         print("evaluated image", f["name"])
            #     index_path = append_index(filesets)
            # print("wrote index at", index_path)
            # print("rate", (time.time() - start) / max_steps)
            
            # testing
            # at most, process the test data once

            start = time.time()
            max_steps = min(examples.steps_per_epoch, max_steps)

            list_rate_pred_err = [] ; list_loss_L1 = []
            list_ssim_it = [] ; list_ssim_io = [] ; list_ssim_to = []
            list_predicted_rate = [] ; list_filenames = []
            fid_rate = open('rate.txt', "a+")
            for step in range(max_steps):
                # results = sess.run(display_fetches)

                def should(freq):
                    # return freq > 0 and ((step + 1) % freq == 0 or step == max_steps - 1)
                    return True

                options = None
                run_metadata = None
                if should(a.trace_freq):
                    options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
                    run_metadata = tf.RunMetadata()


                fetches = {
                    "train": model.train,
                    "global_step": sv.global_step,
                }

                if should(a.progress_freq):
                    fetches["discrim_loss"] = model.discrim_loss
                    fetches["gen_loss_GAN"] = model.gen_loss_GAN
                    fetches["gen_loss_quality"] = model.gen_loss_quality
                    fetches["rate_predictor_loss"] = model.rate_predictor_loss
                    fetches["rate_relative_error"] = model.rate_relative_error
                    fetches["gen_loss_L1"] = model.gen_loss_L1
                    fetches["ssim_it"] = model.ssim_it
                    fetches["ssim_io"] = model.ssim_io
                    fetches["predicted_rate"] = model.predicted_rate

                if should(a.summary_freq):
                    fetches["summary"] = sv.summary_op

                if should(a.display_freq):
                    fetches["display"] = display_fetches



                # list_rate_pred_err = [] ; 
                # summary = sess.run(summary_op)
                # test_summary = tf.Summary()
                # test_summary.ParseFromString(summary)
                # test_summary.value.add(tag='accuracy', simple_value=test_accuracy)
                # test_summary_writer.add_summary(test_summary, global_step)

                # Backup..
                # results = sess.run(fetches, options=options, run_metadata=run_metadata)
                # print("recording summary")
                # sv.summary_writer.add_summary(results["summary"], results["global_step"])


                results = sess.run(fetches, options=options, run_metadata=run_metadata)
                # print("Predicted rate  summary")


                # list_rate_pred_err.append(math.sqrt(results["rate_predictor_loss"]))
                list_rate_pred_err.append(results["rate_relative_error"])
                list_loss_L1.append(results["gen_loss_L1"])

                list_ssim_it.append(results["ssim_it"])
                list_ssim_io.append(results["ssim_io"])
                list_ssim_to.append(results["gen_loss_quality"])


                list_predicted_rate.append(results["predicted_rate"])
                # pdb.set_trace()
                # list_predicted_rate.append(results["predicted_rate"])

                filesets = save_images(results["display"])
                #fid_rate = open('rate.txt', "a+")
                for i, f in enumerate(filesets):
                    list_filenames.append(f["name"])
                    #print("Evaluated image:", f["name"])
                    #print("...Predicted rate:", results["predicted_rate"])
                    #open('rate.txt', "a+").write('{} {}\n'.format(f["name"],results["predicted_rate"])) #added jubran
                    fid_rate.write('{} {}\n'.format(f["name"],results["predicted_rate"])) # jubran
                index_path = append_index(filesets)
                #fid_rate.close() ##jubran
            print("wrote index at", index_path)
            fid_rate.close() ##jubran

            # test_summary = tf.Summary()
            test_summary = tf.Summary()
            avg_rate_pred_err = sum(list_rate_pred_err)/len(list_rate_pred_err)
            avg_loss_L1 = sum(list_loss_L1)/len(list_loss_L1)

            avg_ssim_it = sum(list_ssim_it)/len(list_ssim_it)
            avg_ssim_io = sum(list_ssim_io)/len(list_ssim_io)
            avg_ssim_to = sum(list_ssim_to)/len(list_ssim_to)

            # pdb.set_trace()
            # cmd = 'bash conv_images_to_yuv.sh logs_advtrain_l1_10/images/ yuv_images 512'
            # cmd = 'bash conv_images_to_yuv.sh {}/images/ {} 512'.format(logdir,'yuv_'+logdir)
            # print(cmd)
            # _ = check_output(cmd.split(' '))

            # cmd = './run_vmaf_in_batch list_vmaf_targets_yuv_{}'.format(logdir)
            # vmaf_scores = check_output(cmd.split(' '))
            # avg_vmaf_score_targets = float(str(vmaf_scores).split(':')[-1][:6])     

            # # cmd = 'bash conv_images_to_yuv.sh {}/images/ {} 512'.format(logdir,'yuv_'+logdir)
            # # _ = check_output(cmd.split(' '))
            # cmd = './run_vmaf_in_batch list_vmaf_outputs_yuv_{}'.format(logdir)
            # vmaf_scores = check_output(cmd.split(' '))
            # avg_vmaf_score_outputs = float(str(vmaf_scores).split(':')[-1][:6])     

            # print('VMAF TARGETS',avg_vmaf_score_targets)
            # print('VMAF OUTPUTS',avg_vmaf_score_outputs)

            # test_summary.value.add(tag='VMAF(Input, Target)', simple_value=avg_vmaf_score_targets)
            # test_summary.value.add(tag='VMAF(Input, Output)', simple_value=avg_vmaf_score_outputs)

            test_summary.value.add(tag='SSIM(Input, Target)', simple_value=avg_ssim_it)
            test_summary.value.add(tag='SSIM(Input, Output)', simple_value=avg_ssim_io)
            test_summary.value.add(tag='SSIM(Target, Output)', simple_value=avg_ssim_io)

            test_summary.value.add(tag='Test Rate Relative Error', simple_value=avg_rate_pred_err)
            test_summary.value.add(tag='Test Loss L1', simple_value=avg_loss_L1)
            sv.summary_writer.add_summary(test_summary, results["global_step"])


        else:
            # training
            start = time.time()

            for step in range(max_steps):
                def should(freq):
                    return freq > 0 and ((step + 1) % freq == 0 or step == max_steps - 1)

                options = None
                run_metadata = None
                if should(a.trace_freq):
                    options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
                    run_metadata = tf.RunMetadata()

                fetches = {
                    "train": model.train,
                    "global_step": sv.global_step,
                }

                if should(a.progress_freq):
                    fetches["discrim_loss"] = model.discrim_loss
                    fetches["gen_loss_GAN"] = model.gen_loss_GAN
                    fetches["gen_loss_quality"] = model.gen_loss_quality
                    fetches["rate_predictor_loss"] = model.rate_predictor_loss




                if should(a.summary_freq):
                    fetches["summary"] = sv.summary_op

                if should(a.display_freq):
                    fetches["display"] = display_fetches

                results = sess.run(fetches, options=options, run_metadata=run_metadata)

                if should(a.summary_freq):
                    print("recording summary")
                    sv.summary_writer.add_summary(results["summary"], results["global_step"])

                if should(a.display_freq):
                    print("saving display images")
                    filesets = save_images(results["display"], step=results["global_step"])
                    append_index(filesets, step=True)

                if should(a.trace_freq):
                    print("recording trace")
                    sv.summary_writer.add_run_metadata(run_metadata, "step_%d" % results["global_step"])

                if should(a.progress_freq):
                    # global_step will have the correct step count if we resume from a checkpoint
                    train_epoch = math.ceil(results["global_step"] / examples.steps_per_epoch)
                    train_step = (results["global_step"] - 1) % examples.steps_per_epoch + 1
                    rate = (step + 1) * a.batch_size / (time.time() - start)
                    remaining = (max_steps - step) * a.batch_size / rate
                    print("progress  epoch %d  step %d  image/sec %0.1f  remaining %dm" % (train_epoch, train_step, rate, remaining / 60))
                    print("discrim_loss", results["discrim_loss"])
                    print("gen_loss_GAN", results["gen_loss_GAN"])
                    print("gen_loss_quality", results["gen_loss_quality"])
                    print("rate_predictor_loss", results["rate_predictor_loss"])

                if should(a.save_freq):
                    print("saving model")
                    saver.save(sess, os.path.join(a.output_dir, "model"), global_step=sv.global_step)

                if sv.should_stop():
                    break


main()
