import tensorflow as tf
import transformers
from logger import logger
import pickle
import numpy as np
from keras.layers import Input, Dense

class SentenceModel(tf.keras.Model):

    def __init__(self, modelBase, from_pt=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transformer = transformers.TFAutoModel.from_pretrained(modelBase, from_pt=from_pt)
        

    @tf.function
    def generateSingleEmbedding(self, input, training=False, precision_16 = False):
        
        precision_settings = tf.float16 if precision_16 else tf.float32

        # print("precision_settings: ", precision_settings)
        inds, att = input
        embs = self.transformer({'input_ids': inds, 'attention_mask': att}, training=training)[0]
        outAtt = tf.cast(att, precision_settings)
        sampleLength = tf.reduce_sum(outAtt, axis=-1, keepdims=True)
        maskedEmbs = embs * tf.expand_dims(outAtt, axis=-1)
        # print("="*100)
        # print("Training arg in generateSingleEmbedding of SentenceModel class: ", training)
        # print("="*100)
        return tf.reduce_sum(maskedEmbs, axis=1) / tf.cast(sampleLength, precision_settings)

    @tf.function
    def generateMultipleEmbeddings(self, input, training=False, precision_16 = False):
        # print(len(input))
        precision_settings = tf.float16 if precision_16 else tf.float32
        inds, att = input
        # (batch_size, sequence_length, hidden_size)
        # https://huggingface.co/docs/transformers/model_doc/bert#bertmodel
        # https://huggingface.co/transformers/v3.0.2/model_doc/bert.html
        # last_hidden_state (torch.FloatTensor of shape (batch_size, sequence_length, hidden_size)):
        # Sequence of hidden-states at the output of the last layer of the model.
        # The model outputs a dictionary, and the function retrieves the last_hidden_state, which represents the embeddings for each token in the input sequence.
        

        embs = self.transformer({'input_ids': inds, 'attention_mask': att}, training=training)['last_hidden_state'] 
        # print("="*100)
        # print("Embs:", embs.shape) # Embs: (None, 32, 768)
        # print("Training arg in generateMultipleEmbeddings of SentenceModel class: ", training)
        # print("="*100)

        outAtt = tf.cast(att, precision_settings)
        sampleLength = tf.reduce_sum(outAtt, axis=-1, keepdims=True)
        # print("="*100)
        # print("Att mask:", tf.expand_dims(outAtt, axis=-1).shape) # Att mask: (None, 32, 1)
        # print("="*100)
        maskedEmbs = embs * tf.expand_dims(outAtt, axis=-1)
        return tf.reduce_sum(maskedEmbs, axis=1) / tf.cast(sampleLength, precision_settings)

    @tf.function
    def call(self, inputs, training=False, mask=None):
        # print("="*100)
        # print("Training arg in call of SentenceModel class: ", training)
        # print("="*100)
        return self.generateSingleEmbedding(inputs, training)

    def save_pretrained(self, saveName):
        self.transformer.save_pretrained(saveName)

    def from_pretrained(self, saveName):
        self.transformer = transformers.TFAutoModel.from_pretrained(saveName)


class SentenceModelWithLinearTransformation(SentenceModel):

    def __init__(self, modelBase, embeddingSize=640,precision_16 = False, *args, **kwargs):
        super().__init__(modelBase, *args, **kwargs)

        self.precision_16 = precision_16
        # W = np.random.rand(784, 10)
        # b = np.random.rand(10)
        
        self.postTransformation = tf.keras.layers.Dense(embeddingSize, activation='linear')

        # pickle_file_path = "/home/lenovo/Desktop/arabic_clip/arabert_v2_vit_B_16_plus/phase_1/heads_of_the_model_bert-large-arabertv2-Vit-B-16-plus-240-36_.pickle"

        # logger.info("Finishing load the weights except dense layer")
        # logger.info("Start loading the dense layer weights")
        # with open(pickle_file_path, 'rb') as pickle_file:
        #     loaded_weights = pickle.load(pickle_file)
        #     logger.info(len(loaded_weights))
        #     logger.info(type(loaded_weights))
        #     logger.info(type(loaded_weights[0]))
        #     logger.info(type(loaded_weights[1]))
        #     logger.info(len(loaded_weights[0]))
        #     logger.info(len(loaded_weights[1]))
        #     logger.info("embeddingSize")
        #     logger.info(embeddingSize)

        # self.postTransformation = tf.keras.layers.Dense(embeddingSize, activation='linear')

        # # https://github.com/keras-team/keras/issues/7229
        # # https://keras.io/api/saving/weights_saving_and_loading/

        # # Define the desired shape
        # batch_size = None  # This represents the variable batch size
        # feature_size = 1024  # This represents the feature size

        # a_out = self.postTransformation(tf.convert_to_tensor(tf.ones((128, feature_size), dtype=tf.float16)))

        # # a_out = self.postTransformation(tf.convert_to_tensor([[1]*1024]))

        # self.postTransformation.set_weights([loaded_weights[0], loaded_weights[1]])

        # from keras.layers import Input, Dense
        # import numpy as np
        # from keras.layers import Input, Dense
        # import tensorflow as tf


        # dense_layer = Dense(10, activation='relu')
        
        # print(dense_layer.get_weights())

        # print(len(dense_layer.get_weights()))

        # dense_layer.set_weights([W, b])

        # print(dense_layer.get_weights())

        # logger.info("Finish loading the dense layer weights")

        # print("="*100)
        # print("="*100)
        # print("postTransformation", self.postTransformation)
        # print("="*100)
        # print("="*100)

    @tf.function
    def call(self, inputs, training=False, mask=None):
        # print("="*100)
        # print("Training arg in SentenceModelWithLinearTransformation: ", training)
        # print("Hellllllllllllllllllo")
        # print(type(self.postTransformation(self.generateMultipleEmbeddings(inputs, training))))
        # tensor_output =  self.postTransformation(self.generateMultipleEmbeddings(inputs, training))
        # print(tensor_output.shape)
        # print("Hellllllllllllllllllo")
        # print("="*100)
        # print("self.generateMultipleEmbeddings(inputs, training) shape is: ", self.generateMultipleEmbeddings(inputs, training).shape)

        # self.generateMultipleEmbeddings(inputs, training) shape is:  (None, 768)
        

        return self.postTransformation(self.generateMultipleEmbeddings(inputs, training, precision_16 = self.precision_16))


class SentenceModelWithTanHTransformation(SentenceModel):

    def __init__(self, modelBase, embeddingSize=640, *args, **kwargs):
        super().__init__(modelBase, *args, **kwargs)

        self.postTransformation = tf.keras.layers.Dense(embeddingSize, activation='tanh')
        self.postTransformation2 = tf.keras.layers.Dense(embeddingSize, activation='linear')

    @tf.function
    def call(self, inputs, training=False, mask=None):
        meanEmbedding = self.generateSingleEmbedding(inputs, training)
        d1 = self.postTransformation(meanEmbedding)
        return self.postTransformation2(d1)
