import logging
import os
import sys
from src import Fetcher, ConfigReader, Parser
    
KEY = "KBgNrW8Isjzj5NnnTxIkw7B11bFvHZ4fLPZ4jH9HEGM="
    
'''config
{
    "dateCutoff":null,
    "countCutoff":null,
    "params":{
        "word": "인공지능",
        "astrtCont": "",
        "inventionTitle": "",
        "ipcNumber": "G06N",
        "patent": true,
        "utility": false,
        "lastvalue": "R",
    }
}
'''
    
def setup_logger() -> logging.Logger:
    logger = logging.getLogger("data_fetcher")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len(args) < 1:
        config_dir = os.path.join(os.getcwd(),"configs")
        output_dir = os.path.join(os.getcwd(),"output")
    
    elif len(args) < 2:
        config_dir = args[0]
        output_dir = os.path.join(os.getcwd(),"output")
    else:
        config_dir = args[0]
        output_dir = args[1]

    logger = setup_logger()

    config_reader = ConfigReader(config_dir)
    fetcher = Fetcher(KEY, logger)
    parser = Parser(logger, output_dir)
    
    for config in config_reader.config_gen():
        # Set params for each config
        fetcher.set_params(**config.get("params", {}))
        
        countCutoff = config.get("countCutoff", 500)
        parser.set_cutoff(countCutoff)
        
        # Fetch-parse loop until cutoff is met
        logger.info("Starting fetch-parse loop")
        while True:
            xml_data = fetcher.fetch()
            cutoff_met = parser.parse(xml_data)
            
            if cutoff_met:
                logger.info("Cutoff condition met, stopping fetch-parse loop")
                break
        
        logger.info(f"Completed processing config with {len(parser.parsed_set)} records")