from utils import AvimetryBot
from config import tokens

if __name__ == "__main__":
    avimetry = AvimetryBot()
    avimetry.run(tokens["Avimetry"])
