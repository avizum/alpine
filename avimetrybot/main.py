from utils import AvimetryBot
from config import tokens

if __name__ == "__main__":
    avi = AvimetryBot()
    avi.run(tokens["AvimetryBeta"])
