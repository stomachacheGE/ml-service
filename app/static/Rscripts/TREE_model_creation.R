library(ibmdbR)
mycon <- idaConnect("BLUDB", "", "")
idaInit(mycon)
if (idaModelExists('<model_name>')) {
    drop <- idaDropModel('<model_name>')
}
tr <- idaTree(<targetcolumn>~.,ida.data.frame('<intable>'),id='<primary_key>',model='<model_name>')
cat("{'message':'OK'}")
idaClose(mycon)



