class Concensus:
    def __init__(self, server, baseHash, votes):
        self.server = server
        self.baseHash = baseHash
        self.votes = votes

    def addVote(self):
        self.votes = self.votes + 1
