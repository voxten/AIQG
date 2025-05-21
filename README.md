# txt to sql ai
Download Anaconda and Ollama


## Anaconda
#### Open Anaconda Prompt and run:
#### ``conda create -n nl2sql python=3.10``
#### ``conda activate nl2sql``
#### ``pip install ollama langchain streamlit mysql-connector-python python-dotenv``


## Create Project
#### Open PyCharm → New Project → Select Conda Environment (nl2sql)


#### CMD (Normal CMD)
#### ``ollama pull sqlcoder``


#### Terminals in PyCharm

#### Start Ollama (keep running in background):
#### ``ollama serve``

#### Start project
#### ``streamlit run main.py``