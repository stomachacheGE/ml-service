
# library(ibmdbR)
# mycon <- idaConnect("BLUDB", "","")
# idaInit(mycon)
# modelName <- "TREE_22464_1446045020"
# trCopy <- idaRetrieveModel(modelName)
# df <-data.frame(CUST_ID=c(22),CROSSBUY=c(5))
# idf <- as.ida.data.frame(df,"TREE_22464_1446045020_SCORE",clear.existing=T)
# scores <- predict(trCopy,idf,id="CUST_ID")
# tablename <- as.character(scores@table)
# query <- sprintf("SELECT CLASS FROM %s", tablename) 
# result1 <- idaQuery(query)
# if(is.atomic(result)) {
# 	result <- paste("'",getElement(result1,'CLASS'),"'",sep='')
# } else {
#     result <- paste("'",result$CLASS,"'",sep='',collapse=',')
# }
# cat(paste("{'output':[",result,"]}",sep=''))
# idaDeleteTable(tablename)
# idaClose(mycon)


library(ibmdbR)
mycon <- idaConnect("BLUDB", "","")
idaInit(mycon)
modelName <- "<model_name>"
trCopy <- idaRetrieveModel(modelName)
df <-data.frame(<value>)
idf <- as.ida.data.frame(df,"ML_SERVICE_SCORE",clear.existing=T)
scores <- predict(trCopy,idf,id="ID")
tablename <- as.character(scores@table)
query <- sprintf("SELECT CLASS FROM %s ORDER BY ID ASC", tablename) 
result1 <- idaQuery(query)
if(is.atomic(result1)) {
	result <- paste("'",getElement(result1,'CLASS'),"'",sep='')
} else {
    result <- paste("['",result1$CLASS,"']",sep='',collapse=',')
}
if (<custom_name>) {
	query <- sprintf("RENAME TABLE %s TO <table_name>", tablename)
	rename <- idaQuery(query)
} else {
	idaDeleteTable(tablename)
}
cat(paste("{'output':[",result,"]}",sep=''))
idaDeleteTable("ML_SERVICE_SCORE")
idaClose(mycon)
