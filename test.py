"""This is test module for the app"""
from app.fu import fu
with open('app/sample_models/Drug.str', 'rb') as f:
    model = SPSSModel.create_spss_model('test', fu, 'Drug.str', f)
model
model.__dict__
model.score_hint = "hello"
model.commit()
models =  fu.list_spss_models()
models
model_1 = fu.retrieve_model('test')
model_1.__dict__
model_1.retrieve_metadata()
model_1.__dict__
model_1.commit()
result = model_1.real_time_score(header=["Age", "Sex", "BP", "Cholesterol", "Na", "K"],
data=[ [23, "M", "LOW", "HIGH", 23.5, 23.9] ])
result
records = model_1.get_history()
records
records = model_1.get_history(behaviour='refresh')
records