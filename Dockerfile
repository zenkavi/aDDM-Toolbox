FROM python:2.7.18
RUN apt-get install tk
RUN pip install deap  
RUN pip install future 
RUN pip install matplotlib 
RUN pip install numpy 
RUN pip install pandas 
RUN pip install scipy 
RUN pip install addm_toolbox