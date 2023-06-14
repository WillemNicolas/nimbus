from __future__ import print_function
from dataclasses import dataclass
import json
import os.path as path
import smtplib
from api.providers.DatProvider import DatProvider
from dotenv import dotenv_values
import requests
from api.providers.HtmlProvider import HtmlProvider

from utils.logger import Logger

@dataclass
class PublicationAPI:
    dat_provider : DatProvider
    html_provider : HtmlProvider
    url : str
    api_key : str
    
    def send(self) :
        data = self.merge()
        try :    
            res = requests.post(
                self.url,
                json=data,
                cookies={"access_token":self.api_key}
            )    
            
            if res.status_code == 409:
                response = json.loads(res.text)
                if "requested_id" in response:
                    self.notify(response["requested_id"])
            elif not res.ok :
                Logger.console().error(f"Status code : {res.status_code} for :\n{res.text}")
        except Exception as e:
            Logger.console().error(e)
        
        
    def merge(self) -> dict:
        default_tags= {}
        tags = ["title", "authors_short", "authors_full", "journal", "year", "volume", "pages",\
             "doi", "owner_name", "owner_email", "abstract", "brief_desc", "expts_paper", "expts_web"]
        
        dat_data = self.dat_provider.parse(default_tags,tags)
        data = {}
        #clean dat data
        for file in dat_data:
            data[file] = {}
            for key,value in dat_data[file].items():
                if value is not None and value != "" and value != []:
                    data[file][key] = value
        #print("DAT :")
        #print(dat_data)
        
        #si 3eme colonne

        html_data = self.html_provider.parse(default_tags,tags)
        #clean html data
        for file in html_data:
            if not file in data.keys():
                data[file] = {}
            for key,value in html_data[file].items():
                if value is not None and value != "" and value != []:
                    data[file][key] = value
        
        data = list(data.values())
        
        #grep all exp ids
        _exp_ids = [publication["expts_web"] for publication in data]
        exp_ids = []
        for ids in _exp_ids:
            exp_ids.extend(ids)
        exp_ids = list(set(exp_ids))
        
        data = {
            "publications" : data,
            "exp_ids" : exp_ids,
        }

        return data
        
    def notify(self,requested_exp_ids:list) :
        
        f = open("request_ids.json", "w+")
        s = f.read()
        content = json.loads(s) if s != "" else {}
        if "request_ids" in content :
            ids = set(content["request_ids"])
            ids.update(requested_exp_ids)
            requested_exp_ids = list(ids)
        f.write(json.dumps({"request_ids" : requested_exp_ids}))
        Logger.console().warning(f"requested ids are : {requested_exp_ids}")
     
        
    
    @staticmethod
    def build(filepath : str) -> 'PublicationAPI':
        if not path.exists(filepath):
            dat_provider = DatProvider([])
            html_provider, ok = HtmlProvider.build_from_src(filepath)
            if not ok :
                raise Exception(f"{filepath} does not exist or not accessible")
        else :
            dat_provider = DatProvider.build(filepath)
            html_provider = HtmlProvider.build(filepath)

        route = "insert/publication"
        config = dotenv_values(".env")
        url = f"{config['ARCHIVE_DB_URL']}/{route}"
        api_key = config['API_KEY']
        
        return PublicationAPI(
            dat_provider = dat_provider,
            html_provider = html_provider,
            url = url,
            api_key = api_key,
        )