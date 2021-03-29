class Concensus:
    def __init__(self, baseHash, votes, server="main"):
        self.server = server
        self.baseHash = baseHash
        self.votes = votes

    def addVote(self):
        self.votes = self.votes + 1

    def validateMain(self):
        return self.server == "main"
