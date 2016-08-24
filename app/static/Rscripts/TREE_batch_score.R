library(ibmdbR)
mycon <- idaConnect("BLUDB", "", "")
idaInit(mycon)
tr <- idaRetrieveModel('<model_name>')
scores <- predict(tr,ida.data.frame('<intable>'),id='<primary_key>')
scorestable <- as.character(scores@table)
if (<custom_name>) {
query <- sprintf("RENAME TABLE %s TO <table_name>", scorestable)
idaQuery(query)
scorestable <-  as.character('<table_name>')
}
cat(paste("{'message':'OK','table_name':'",scorestable,"'}",sep=''))
idaClose(mycon)

# library(ibmdbR)
# mycon <- idaConnect("BLUDB", "", "")
# idaInit(mycon)
# tr <- idaRetrieveModel('WWW')
# scores <- predict(tr,ida.data.frame('SAMPLES.CUSTOMER_ACQUISITION'),id='CUST_ID')
# scorestable <- as.character(scores@table)
# if (FALSE) {
# query <- sprintf("RENAME TABLE %s TO NAME_TEST", scorestable)
# idaQuery(query)
# scorestable <-  as.character("NAME_TEST")
# }
# cat(paste("{'message':'OK','table_name':'",scorestable,"'}",sep=''))
# idaClose(mycon)
