from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import re
import time
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
from scipy.special import softmax
from apify_client import ApifyClient
import json


class WebPurify(APIView):
    def post(self, request):
        try:
            image_file = request.FILES.get('input')

            # Read the binary data of the uploaded file
            image_data = image_file.read()

            picpurify_url = 'https://www.picpurify.com/analyse/1.1'
            img_data = {'file_image': image_data}

            result_data = requests.post(picpurify_url, files=img_data, data={"API_KEY": picPurify, "task": "porn_moderation,suggestive_nudity_moderation,gore_moderation,money_moderation,weapon_moderation,drug_moderation,hate_sign_moderation,obscene_gesture_moderation"})
            
            # Convert the JSON string into a Python dictionary
            result_json = json.loads(result_data.content)

            return Response({'status': 200, 'data': result_json})
        except Exception as e:
            return Response({'status': 400, 'message': 'Error: ' + str(e)})



class CommentProcessing(APIView):
    def __init__(self):
        self.MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL)
    
    def computeFinalScore(self,scores):
        # print(scores)
        neg,pos,neu=0,0,0
        for score in scores:
            neg+=score['neg']
            neu+=score['neu']
            pos+=score['pos']
        
        return [{'neg':neg/len(scores),'neu':neu/len(scores),'pos':pos/len(scores)}]


    def getNLP(self,responseList):
        try:
            #Running comments on ROBERTA
            finalScores = []
            for response in responseList:
                encoded = (self.tokenizer(response,return_tensors='pt'))
                output = self.model(**encoded)
                scores = output[0][0].detach().numpy()
                scores = softmax(scores)
                scores_dict = {
                    'neg': scores[0],
                    'neu':scores[1],
                    'pos':scores[2]
                }
                finalScores.append(scores_dict)
            result = self.computeFinalScore(finalScores)
            return result
        except Exception as e:
            return str('Exception: {e}')
            
    
    def post(self,request):
        try:
            link = request.data['link']
            if not link:
                return Response({'status':400,'message':'Error(Invalid Link)'})
            # Initialize the ApifyClient with your API token
            client = ApifyClient(tokenAPIFY)

            # Prepare the Actor input
            run_input = {
                "directUrls": [
                    link,
                ],
                "resultsLimit": 50,
            }

            # Run the Actor and wait for it to finish
            run = client.actor("SbK00X0JYCPblD2wp").call(run_input=run_input)

            # Fetch and print Actor results from the run's dataset (if there are any)
            output = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                output.append(item['text'])
            
            result = self.getNLP(output)
                
            return Response({'status':200,'output':result})
        except:
            return Response({'status':400,'output':'Error'})


class HateSpeechAPI(APIView):
    def NLP(self,message):
        API_URL = "https://api-inference.huggingface.co/models/gportillac/Case_03_Natural_Language_Processing_Class"
        headers = {"Authorization": f'Bearer {Bearer_Token}'}

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
            
        output = query({
            "inputs": message,
        })
        # Label_1:Positive and Label_0:Negative
        return output
    
    def hate_speech_detection(self,data):
        try:
            API_URL = "https://api-inference.huggingface.co/models/unhcr/hatespeech-detection"
            headers = {"Authorization": f'Bearer {Bearer_Token}'}

            def query(payload):
                response = requests.post(API_URL, headers=headers, json=payload)
                return response.json()
                
            output = query({
                "inputs": data,
            })

            try:
                while True:
                    if output['message']['error'] == 'Model unhcr/hatespeech-detection is currently loading':
                        time.sleep(10)
                        output = query({
                            "inputs": data,
                        })
                    else:
                        break
                    
            except:
                pass
            return output
        except:
            return None

    def post(self,request):
        try:
            image_file = request.FILES.get('input') 
            print(image_file)
            if not image_file:
                return Response({'status': 400, 'message': 'Image file not provided'})

            API_URL = "https://api-inference.huggingface.co/models/jinhybr/OCR-Donut-CORD"
            headers = {"Authorization": f'Bearer {Bearer_Token}'}

            def query(image):
                data = image.read()
                response = requests.post(API_URL, headers=headers, data=data)
                return response.json()
            
            def refine(reply):
                pattern = r'>(.*?)<'
                matches = re.findall(pattern,reply)
                ans = ""
                for i in matches:
                    if i!="":
                        ans+=i+" "
                return ans
            
            output = query(image_file)
            data = (refine(str(output[0]['generated_text'])))
            
            try:
                while True:
                    if output['message']['error'] == 'Model jinhybr/OCR-Donut-CORD is currently loading':
                        time.sleep(10)
                        output = query(image_file)
                        data = (refine(str(output[0]['generated_text'])))
                    else:
                        break
            except:
                pass
            
            response = self.hate_speech_detection(data)
            emotion = self.NLP(data)
            
            return Response({'status':200,'output':output,'message':data,'response':response,'emotion':emotion})
        except:
            return Response({'status':400,'message':output})
        
    
