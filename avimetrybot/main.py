from utils.utility import AvimetryBot
from dotenv import load_dotenv
import os

load_dotenv()
avitoken = os.getenv('Bot_Token')

if __name__=="__main__":
    avimetry=AvimetryBot()
    avimetry.run(avitoken)