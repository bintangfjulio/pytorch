import emoji
import re
import torch
import pandas as pd

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from transformers import BertTokenizer
from torch.utils.data import TensorDataset


class Preprocessor:
    def __init__(self, bert_model, max_length):
        self.stop_words = StopWordRemoverFactory().get_stop_words()
        self.tokenizer = BertTokenizer.from_pretrained(bert_model, use_fast=False)
        self.stemmer = StemmerFactory().create_stemmer()
        self.max_length = max_length

    def text_processing(self, data):
        text = str(data["kata_kunci"]) + " - " + str(data["abstrak"])
        text = text.lower()
        text = emoji.replace_emoji(text, replace='') 
        text = re.sub(r'\n', ' ', text) 
        text = re.sub(r'http\S+', '', text)  
        text = re.sub(r'\d+', '', text)  
        text = re.sub(r'[^a-zA-Z ]', '', text)  
        text = ' '.join([word for word in text.split() if word not in self.stop_words])  
        text = self.stemmer.stem(text)
        text = text.strip()      
        token = self.tokenizer(text=text, max_length=self.max_length, padding="max_length", truncation=True) 

        return token['input_ids'], token['attention_mask']
    
    def get_labels(self, dataset, target):
        labels = dataset[target].unique().tolist()
        labels = sorted(labels)
        
        return labels
    
    def get_grouped_labels(self, dataset, root, node):
        node_labels = dataset.groupby(root)[node].unique().apply(sorted).to_dict()
        root_labels = list(node_labels.keys())
        
        return root_labels, node_labels
    
    def train_test_split(dataset, test_size, add_id_tes):
        dataset = dataset.sample(frac=1)
        train_valid_size = round(dataset.shape[0] * (1.0 - test_size))
        train_valid_set = pd.DataFrame(dataset.iloc[:train_valid_size, :])
        df_test = pd.DataFrame(dataset.iloc[train_valid_size:, :])

        if add_id_tes:
            df_test['id_test'] = df_test.reset_index().index + 1

        test_set = TensorDataset(torch.tensor(df_test['input_ids'].tolist()), df_test['attention_mask'].tolist(), torch.tensor(df_test['target'].tolist()))

        return train_valid_set, test_set