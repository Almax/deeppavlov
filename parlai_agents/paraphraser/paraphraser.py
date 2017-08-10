import copy

from . import config
from .model import ParaphraserModel
from .utils import load_embeddings

from keras.preprocessing.sequence import pad_sequences

from parlai.core.agents import Agent
from parlai.core.dict import DictionaryAgent
from parlai.core.params import class2str



class ParaphraserDictionaryAgent(DictionaryAgent):

    @staticmethod
    def add_cmdline_args(argparser):
        group = DictionaryAgent.add_cmdline_args(argparser)
        group.add_argument(
            '--dict_class', default=class2str(ParaphraserDictionaryAgent)
        )

    def act(self):
        """Add only words passed in the 'text' field of the observation to this dictionary."""
        text = self.observation.get('text')
        if text:
            self.add_to_dict(self.tokenize(text))
        return {'id': 'ParaphraserDictionary'}


class ParaphraserAgent(Agent):

    @staticmethod
    def add_cmdline_args(argparser):
        config.add_cmdline_args(argparser)
        ParaphraserAgent.dictionary_class().add_cmdline_args(argparser)

    @staticmethod
    def dictionary_class():
        return ParaphraserDictionaryAgent

    def __init__(self, opt, shared=None):
        self.id = 'ParaphraserAgent'
        self.episode_done = True
        super().__init__(opt, shared)
        self.word_dict = ParaphraserAgent.dictionary_class()(opt)
        self.embedding_matrix = load_embeddings(opt, self.word_dict.tok2ind)
        self.model = ParaphraserModel(self.word_dict, self.embedding_matrix, opt)
        self.n_examples = 0

    def observe(self, observation):
        observation = copy.deepcopy(observation)
        if not self.episode_done:
            # if the last example wasn't the end of an episode, then we need to
            # recall what was said in that example
            prev_dialogue = self.observation['text']
            observation['text'] = prev_dialogue + '\n' + observation['text']
        self.observation = observation
        self.episode_done = observation['episode_done']
        return observation

    def act(self):
        # call batch_act with this batch of one
        return self.batch_act([self.observation])[0]

    def batch_act(self, observations):
        batch_size = len(observations)
        # initialize a table of replies with this agent's id
        batch_reply = [{'id': self.getID()} for _ in range(batch_size)]
        examples = [self._build_ex(obs) for obs in observations]
        batch = self._batchify(examples)

        if 'labels' in observations[0]:
            self.n_examples += len(examples)
            self.model.update(batch)
        else:
            predictions = self.model.predict(batch)
            for i in range(len(predictions)):
                batch_reply[i]['text'] = predictions[i]

        return batch_reply

    def _build_ex(self, ex):
        """Find the token span of the answer in the context for this example.
        """
        inputs = dict()
        inputs['question1'] = ex['text'].split('\n')[1]
        inputs['question2'] = ex['text'].split('\n')[2]
        if 'labels' in ex:
            inputs['labels'] = ex['labels']

        return inputs

    def _batchify(self, batch):
        question1 = [self.word_dict.txt2vec(ex['question1']) for ex in batch]
        question2 = [self.word_dict.txt2vec(ex['question2']) for ex in batch]
        question1 = pad_sequences(question1, maxlen=self.opt['max_sequence_length'])
        question2 = pad_sequences(question2, maxlen=self.opt['max_sequence_length'])
        if len(batch[0]) == 3:
            y = [1 if ex['labels'][0] == 'Да' else 0 for ex in batch]
            return [question1, question2], y
        else:
            return [question1, question2]

    def _predictions2text(self, predictions):
        y = ['Да' if ex == 1 else 'Нет' for ex in predictions]
        return y

    def report(self):
        return (
            '[train] updates = %d | train loss = %.2f | exs = %d' %
            (self.model.updates, self.model.train_loss.avg, self.n_examples)
            )

