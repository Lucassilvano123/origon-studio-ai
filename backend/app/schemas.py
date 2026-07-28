from pydantic import BaseModel, Field, HttpUrl
from typing import Any
class ProductIn(BaseModel):
    name:str=Field(min_length=2,max_length=160); category:str='Outros'; description:str=''; benefits:str=''; audience:str=''; source_url:str=''; price:str=''
class ProjectIn(BaseModel):
    product_id:int; name:str; platform:str='shopee'; mode:str='assisted'; duration:int=15; versions:int=Field(default=3,ge=1,le=5); language:str='pt-BR'
class BatchIn(BaseModel):
    name:str; product_ids:list[int]=Field(min_length=1,max_length=5); versions:int=Field(default=3,ge=1,le=5)
class ImportUrlIn(BaseModel): url:HttpUrl
class GenerateIn(BaseModel): project_id:int
class SettingIn(BaseModel): value:Any
