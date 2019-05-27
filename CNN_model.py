import torch
import torch.nn as nn
from attention import Attention, NewAttention, StackAttention1
from language_model import WordEmbedding, QuestionEmbedding1, QuestionEmbedding
from classifier import SimpleClassifier
from fc import FCNet


class CNNModel(nn.Module):
    def __init__(self, w_emb, q_emb1, q_emb2, v_att, q_net, v_net, classifier, linear_v, linear_q):
        super(CNNModel, self).__init__()
        self.w_emb = w_emb
        self.q_emb1 = q_emb1
        self.q_emb2 = q.emb2
        self.v_att = v_att
        self.q_net = q_net
        self.v_net = v_net
        self.classifier = classifier
        self.linear_v = linear_v
        self.linear_q = linear_q

    def forward(self, v, b, q, labels):
        """Forward

        v: [batch, num_objs, obj_dim]
        b: [batch, num_objs, b_dim]
        q: [batch_size, seq_length]

        return: logits, not probs
        """
        w_emb = self.w_emb(q)  # [batch, seq, 300]
        q_emb1 = self.q_emb1(w_emb)  # [batch, q_dim]
        q_emb2 = self.q_emb2(w_emb) # [batch, q_dim]

        q_emb = torch.cat((q_emb1, q_emb2), 1) # [batch, 2*q_dim]

        v_emb = self.linear_v(v)  # [batch, 2*num_hid]
        q_emb = self.linear_q(q_emb) # [batch, 2*num_hid]

        # stack 1
        att = self.v_att(v_emb, q_emb)
        v_emb1 = (att * v).sum(1)  # [batch, v_dim]

        q_repr = self.q_net(q_emb)  # [batch, num_hid]
        v_repr = self.v_net(v_emb1)  # [batch, num_hid]

        joint_repr = q_repr * v_repr

        logits = self.classifier(joint_repr)
        # print(logits.shape)
        return logits


def build_baseline0(dataset, num_hid):
    w_emb = WordEmbedding(dataset.dictionary.ntoken, 300, 0.0)
    q_emb1 = QuestionEmbedding1(300)
    q_emb2 = QuestionEmbedding(300, num_hid, 1, False, 0.0)
    v_att = StackAttention1(num_hid, num_hid, num_hid)
    q_net = FCNet([num_hid, num_hid])
    v_net = FCNet([dataset.v_dim, num_hid])
    linear_v = torch.nn.Linear(dataset.v_dim, num_hid)
    linear_q = torch.nn.Linear(2*num_hid, num_hid)
    classifier = SimpleClassifier(
        num_hid, 2 * num_hid, dataset.num_ans_candidates, 0.5)
    return CNNModel(w_emb, q_emb1, q_emb2, v_att, q_net, v_net, classifier, linear_v, linear_q)

