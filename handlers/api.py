import json
import cgi
import webapp2
from models import Citizen
from models import CitizenHelper
from models import Evaluation
from handlers import Mutation

class SaveCitizen(webapp2.RequestHandler):
    def post(self):
        print "In SaveCitizen"
        s = self.request.get("data")
        data = json.loads(s)
        citizenID = data["citizenID"]
        generationID = data["generationID"]
        evaluationDict = data["evaluation"]
        response_obj={}
        if not citizenID or len(citizenID) == 0:
            response_obj["response_code"] = 1
            response_obj["error_msg"] = "Citizen ID missing"
            self.response.write(json.dumps(response_obj))
            return
        citizenID = int(citizenID)
        if not generationID or len(generationID) == 0:
            response_obj["response_code"] = 1
            response_obj["error_msg"] = "Generation ID missing"
            self.response.write(json.dumps(response_obj))
            return
        generationID = int(generationID)
        citizen = Citizen.Citizen.get_citizen(generationID, citizenID)
        if not citizen:
            response_obj["response_code"] = 1
            response_obj["error_msg"] = "Citizen doesn't exist"
            self.response.write(json.dumps(response_obj))
            return
        if not evaluationDict:
            response_obj["response_code"] = 1
            response_obj["error_msg"] = "No evaluation given"
            self.response.write(json.dumps(response_obj))
            return
        evaluationObj = Evaluation.Evaluation()
        evaluationObj.startTime = evaluationDict["startMs"]
        evaluationObj.startTime = evaluationDict["startMs"]
        evaluationObj.endTime = evaluationDict["endMs"]
        evaluationObj.evaluationScore = evaluationDict["surveyScore"]
        evaluationObj.clicks = evaluationDict["clicks"]
        citizen.state = 2
        citizen.evaluation = evaluationObj
        citizen.put()
        print "Here 1"
        response_obj["response_code"] = 0
        response_obj["message"] = "Saved Citizen Successfully"
        self.response.write(json.dumps(response_obj))
        # Just mutate one citizen
        # new_cit = Mutation.Mutation.mutateSingleCitizen(citizen)
        # new_cit.generationID = 2
        # new_cit.citizenID = 1
        # new_cit.state = 0
        # new_cit.put()
        # print new_cit
        gen_citizens = Citizen.Citizen.get_latest_generation_citizens()
        all_evaluated = True
        for citizen in gen_citizens:
            if citizen.state != 2:
                all_evaluated = False
                break
        if all_evaluated:
            print "Running the mutation algorithm"
            Mutation.Mutation.generateNextGeneration()
        else:
            print "Not running mutation algorithm"
        return

class FetchCitizen(webapp2.RequestHandler):
    def post(self):
        genCitizens = Citizen.Citizen.get_latest_generation_citizens()
        toSendCitizen = None
        for citizen in genCitizens:
            if citizen.state == 0:
                toSendCitizen = citizen
                break
        response_obj = {}
        response_obj["response_code"] = 0
        if toSendCitizen is None:
            response_obj["citizen"] = "null"
        else:
            print "Fetching citizen"
            print toSendCitizen.generationID
            print toSendCitizen.citizenID
            toSendCitizen.state = 1
            toSendCitizen.put()
            citizen = {}
            citizen["state"] = toSendCitizen.state
            citizen["citizenID"] = toSendCitizen.citizenID
            citizen["generationID"] = toSendCitizen.generationID
            citizen["numrows"] = toSendCitizen.numRows
            citizen["numcols"] = toSendCitizen.numCols
            citizen["evaluation"] = None
            citizen["fourPointClasser"] = toSendCitizen.fourPointClasses.toDict()
            citizen["classPool"] = toSendCitizen.classPoolList()
            citizen["cellData"] = toSendCitizen.cellDataList()
            response_obj["citizen"] = citizen
        self.response.write(json.dumps(response_obj))
        return

class SaveNewCitizen(webapp2.RequestHandler):
    def post(self):
        s = self.request.get("data")
        data = json.loads(s)
        response_obj={}
        citizen = Citizen.Citizen()
        gen_citizens = Citizen.Citizen.get_all_citizens_by_generation(1)
        citID = 1
        if gen_citizens:
            for cit in gen_citizens:
                if cit.citizenID >= citID:
                    citID = cit.citizenID + 1
        citizen.state = 0
        citizen.generationID = 1
        citizen.citizenID = citID
        citizen.numRows = data["numrows"]
        citizen.numCols = data["numcols"]
        citizen.evaluation = None
        fourPointDict = data["fourPointClasser"]
        citizen.fourPointClasses = CitizenHelper.FourPointClassifier()
        citizen.fourPointClasses.regionClasses = fourPointDict["classes"]
        citizen.fourPointClasses.north = fourPointDict["n"]
        citizen.fourPointClasses.south = fourPointDict["s"]
        citizen.fourPointClasses.east = fourPointDict["e"]
        citizen.fourPointClasses.west = fourPointDict["w"]
        classPoolObj = data["classPool"]
        citizen.classPool = []
        for cP in classPoolObj:
            cPObj = CitizenHelper.Perceptron()
            cPObj.pool = cP
            citizen.classPool.append(cPObj)
        cells = data["cellData"]
        citizen.cellData = []
        for cellD in cells:
            cell = CitizenHelper.Cell()
            cell.bias = cellD["bias"]
            cell.x = cellD["x"]
            cell.y = cellD["y"]
            cell.z = cellD["z"]
            cell.wrap = cellD["wrap"]
            cell.origActivation = cellD["origActivation"]
            cell.classPoolIndex = cellD["classPoolIndex"]
            citizen.cellData.append(cell)
        citizen.put()
        response_obj["response_code"] = 0
        response_obj["message"] = "Saved New Citizen Successfully"
        self.response.write(json.dumps(response_obj))
        return

class GenerateACitizen(webapp2.RequestHandler):
    def get(self):
        citizen = Mutation.Mutation.createRandomNewCitizen(Mutation.ROWS, Mutation.COLS, Mutation.NUM_OBJ_CLASSES, Mutation.WGT_POOL_SIZE)
        citizen.state = 0
        citizen.citizenID = 1
        citizen.generationID = 0
        citizen.put()
        response_obj = {}
        response_obj["response_code"] = 0
        response_obj["msg"] = "Citizen generated"
        response_obj["cID"] = citizen.citizenID
        response_obj["gID"]  = citizen.generationID
        self.response.write(json.dumps(response_obj))
        return

class GenerateFirstGen(webapp2.RequestHandler):
    def get(self):
        for i in range(0, 10):
            citizen = Citizen.Citizen.createRandomNewCitizen(Citizen.ROWS, Citizen.COLS, Citizen.NUM_OBJ_CLASSES, Citizen.WGT_POOL_SIZE)
            citizen.state = 0
            citizen.citizenID = i+1
            citizen.generationID = 1
            citizen.put()
        response_obj = {}
        response_obj["response_code"] = 0
        response_obj["msg"] = "Citizen generated"
        response_obj["cID"] = citizen.citizenID
        response_obj["gID"]  = citizen.generationID
        self.response.write(json.dumps(response_obj))
        return

app = webapp2.WSGIApplication([('/api/save', SaveCitizen), ('/api/fetch', FetchCitizen), ('/api/genfirstgeneration', GenerateFirstGen),
                               ('/api/newcitizen', SaveNewCitizen), ('/api/generatecitizen', GenerateACitizen)], debug=True)
