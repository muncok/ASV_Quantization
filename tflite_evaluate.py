import numpy as np
import argparse
import tensorflow as tf

from data.dataset import Voxceleb1


parser = argparse.ArgumentParser("evaluate tflite model")
parser.add_argument("-tflite_file", type=str, required=True)
parser.add_argument("-quantize", action='store_true')
parser.add_argument("-n_test", type=int, default=50)
args = parser.parse_args()

tflite_file = args.tflite_file
n_test = args.n_test

dataset = Voxceleb1("/tmp/sv_set/voxc1/fbank64")
test_x, test_y = dataset.get_norm("dev/test", scale=24)
test_x = test_x[:n_test]
test_y = test_y[:n_test]

def quantize(detail, data):
    shape = detail['shape']
    dtype = detail['dtype']
    a, b = detail['quantization']

    return (data/a + b).astype(dtype).reshape(shape)

def dequantize(detail, data):
    a, b = detail['quantization']

    return (data - b)*a

#####################################################
# TFLite Interpreter
#####################################################

# load TFLite file
interpreter = tf.lite.Interpreter(model_path=tflite_file)
# Allocate memory.
interpreter.allocate_tensors()

# get some informations.
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

#####################################################
# Inference
#####################################################
n_corrects = 0
if args.quantize:
    # print('quant_stat', input_details[0]['quantization'])
    for x, y in zip(test_x, test_y):
        x = np.expand_dims(x, 0)
        x = quantize(input_details[0], x)
        interpreter.set_tensor(input_details[0]['index'], x)
        interpreter.invoke()

        # The results are stored on 'index' of output_details
        output_ = interpreter.get_tensor(output_details[0]['index'])
        output_ = dequantize(output_details[0], output_)
        pred = output_.argmax()
        print(pred, y)
        if pred == y:
            n_corrects += 1
else:
    for x, y in zip(test_x, test_y):
        x = np.expand_dims(x, 0)
        interpreter.set_tensor(input_details[0]['index'], x)
        interpreter.invoke()

        # The results are stored on 'index' of output_details
        output_ = interpreter.get_tensor(output_details[0]['index'])
        pred = output_.argmax()
        print(pred, y)
        if pred == y:
            n_corrects += 1

print("Correct/Trial: {}/{}".format(n_corrects, n_test))

