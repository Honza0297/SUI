import torch
import torch.nn.functional as F
import numpy as np
import copy

NB_FEAS = 11

class dataset:
    def __init__(self, positives, negatives):
        self.pos = np.genfromtxt(positives, delimiter=",")
        #self.pos = np.delete(self.pos, -1, axis=1)
        self.neg = np.genfromtxt(negatives, delimiter=",")
        #self.neg = np.delete(self.neg, -1, axis=1)
        self.xs = np.ndarray(shape=(len(self.pos)+len(self.neg),NB_FEAS), buffer=np.r_[self.pos, self.neg])
        self.targets = np.r_[np.ones(len(self.pos)), np.zeros(len(self.neg))]


def evaluate(classifier, inputs, targets):
    return np.sum(abs(classifier.prob_class_1(inputs)-targets) < 0.5) / float(len(targets))


class LogisticRegressionMulti(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.w = torch.nn.parameter.Parameter(torch.tensor([1.0]))
        self.b = torch.nn.parameter.Parameter(torch.tensor([0.0]))

        self.linear = torch.nn.Linear(NB_FEAS ,1)

    def forward(self, x):
        return torch.squeeze(torch.sigmoid(self. w *self.linear(x) + self.b))


    def prob_class_1(self, x):
        prob = self(torch.from_numpy(x.astype("float")).float())
        return prob.detach().numpy()


def batch_provider_multi(xs, targets, batch_size=10):
    indices = np.random.randint(0, len(targets), batch_size)
    for start in range(0, len(xs), batch_size):
        yield torch.tensor(xs[indices], dtype=torch.float), \
              torch.tensor(targets[indices], dtype=torch.float)


def train_multiple_llr(nb_epochs, lr, batch_size):
    ''' nb_epochs -- how many times to go through the full training data
        lr -- learning rate
        batch_size -- size of minibatches
    '''
    model = LogisticRegressionMulti()
    best_model = copy.deepcopy(model)
    losses = []
    accuracies = []
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = F.binary_cross_entropy

    for i in range(nb_epochs):
        print("Start epoch number", i)
        accumulated_loss = 0
        for x, t in batch_provider_multi(train_dataset.xs, train_dataset.targets, batch_size):
            optimizer.zero_grad()
            outputs = model(x)

            loss = criterion(outputs, torch.squeeze(t))
            accumulated_loss += loss
            loss.backward()
            optimizer.step()
        losses.append(accumulated_loss / batch_size / 100)
        temp = evaluate(model, val_dataset.xs, val_dataset.targets)
        accuracies.append(temp)
        print("# Current accurancy is: {}".format(temp))
        if temp == max(accuracies):

                best_model = copy.deepcopy(model)

    return best_model, losses, accuracies


if __name__ == "__main__":

    train_dataset = dataset("positives.trn", "negatives.trn")
    val_dataset = dataset("positives.val", "negatives.val")

    epochs = 10000
    lr = 0.05
    batch_size = 10000
    with torch.no_grad():
        model, losses, accuracies = train_multiple_llr(epochs, lr, batch_size)
    print("max accuracy is", max(accuracies))
    print("accuracies", accuracies)
    torch.save(model.state_dict(), "fea11.pt")

