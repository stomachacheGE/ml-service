library(ibmdbR)
mycon <- idaConnect("BLUDB", "", "")
idaInit(mycon)
models <- idaListModels()
tr <- models[(models$ALGORITHM=='Regression Tree') | (models$ALGORITHM=='Decision Tree'),]
models <- paste("'",tr$MODELNAME,"'",sep='',collapse=",")
cat(paste("{'models':[",models,"]}",sep=''))
idaClose(mycon)
