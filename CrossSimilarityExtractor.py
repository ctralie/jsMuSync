import numpy as np
import sys
sys.path.append("GeometricCoverSongs")
sys.path.append("GeometricCoverSongs/SequenceAlignment")
import os
import scipy.io as sio
import scipy.misc
import time
import matplotlib.pyplot as plt
from CSMSSMTools import *
from BlockWindowFeatures import *
from Covers80Experiments import *
import json


def getBase64File(filename):
    fin = open(filename, "rb")
    b = fin.read()
    b = b.encode("base64")
    fin.close()
    return b

def getBase64PNGImage(D, cmapstr):
    c = plt.get_cmap(cmapstr)
    D = np.round(255.0*D/np.max(D))
    C = c(np.array(D, dtype=np.int32))
    scipy.misc.imsave("temp.png", C)
    b = getBase64File("temp.png")
    os.remove("temp.png")
    return b

#http://stackoverflow.com/questions/1447287/format-floats-with-standard-json-module
class PrettyFloat(float):
    def __repr__(self):
        return '%.4g' % self
def pretty_floats(obj):
    if isinstance(obj, float):
        return PrettyFloat(obj)
    elif isinstance(obj, dict):
        return dict((k, pretty_floats(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return map(pretty_floats, obj)
    return obj

def compareTwoSongsJSON(filename1, TempoBias1, filename2, TempoBias2, hopSize, FeatureParams, CSMTypes, Kappa, outfilename, song1name = 'Song 1', song2name = 'Song 2'):
    print "Getting features for %s..."%filename1
    (XAudio, Fs) = getAudio(filename1)
    (tempo, beats1) = getBeats(XAudio, Fs, TempoBias1, hopSize)
    (Features1, O1) = getBlockWindowFeatures((XAudio, Fs, tempo, beats1, hopSize, FeatureParams))

    print "Getting features for %s..."%filename2
    (XAudio, Fs) = getAudio(filename2)
    (tempo, beats2) = getBeats(XAudio, Fs, TempoBias2, hopSize)
    (Features2, O2) = getBlockWindowFeatures((XAudio, Fs, tempo, beats2, hopSize, FeatureParams))

    print "Feature Types: ", Features1.keys()

    beats1 = beats1*hopSize/float(Fs)
    beats2 = beats2*hopSize/float(Fs)
    Results = {'song1name':song1name, 'song2name':song2name, 'hopSize':hopSize, 'FeatureParams':FeatureParams, 'Kappa':Kappa, 'CSMTypes':CSMTypes, 'beats1':pretty_floats(beats1.tolist()), 'beats2':pretty_floats(beats2.tolist())}
    #Do each feature individually
    FeatureCSMs = {}
    for FeatureName in Features1:
        print "Doing %s..."%FeatureName
        res =  getCSMSmithWatermanScores([Features1[FeatureName], O1, Features2[FeatureName], O2, Kappa, CSMTypes[FeatureName]], True)
        CSMs = {}
        CSMs['D'] = getBase64PNGImage(res['D'], 'afmhot')
        CSMs['CSM'] = getBase64PNGImage(res['CSM'], 'afmhot')
        CSMs['DBinary'] = getBase64PNGImage(1-res['DBinary'], 'gray')
        CSMs['score'] = res['score']
        FeatureCSMs[FeatureName] = CSMs;

    #Do OR Merging
    print "Doing OR Merging..."
    res = getCSMSmithWatermanScoresORMerge([Features1, O1, Features2, O2, Kappa, CSMTypes], True)
    CSMs = {}
    CSMs['D'] = getBase64PNGImage(res['D'], 'afmhot')
    CSMs['CSM'] = getBase64PNGImage(1-res['DBinary'], 'gray')
    CSMs['DBinary'] = CSMs['CSM']
    CSMs['score'] = res['score']
    CSMs['FeatureName'] = 'ORFusion'
    FeatureCSMs['ORFusion'] = CSMs

    #Do cross-similarity fusion
    print "Doing similarity network fusion..."
    K = 20
    NIters = 3
    res = getCSMSmithWatermanScoresEarlyFusionFull([Features1, O1, Features2, O2, Kappa, K, NIters, CSMTypes], True)
    CSMs = {}
    CSMs['D'] = getBase64PNGImage(res['D'], 'afmhot')
    CSMs['CSM'] = getBase64PNGImage(res['CSM'], 'afmhot')
    CSMs['DBinary'] = getBase64PNGImage(1-res['DBinary'], 'gray')
    CSMs['score'] = res['score']
    FeatureCSMs['SNF'] = CSMs

    Results['FeatureCSMs'] = FeatureCSMs
    #Add music as base64 files
    Results['file1'] = getBase64File(filename1)
    Results['file2'] = getBase64File(filename2)
    fout = open(outfilename, "w")
    fout.write(json.dumps(Results))
    fout.close()

if __name__ == '__main__':
    Kappa = 0.1
    hopSize = 512
    TempoBias1 = 180
    TempoBias2 = 180

    fin = open('covers32k/list1.list', 'r')
    files1 = [f.strip() for f in fin.readlines()]
    fin.close()
    fin = open('covers32k/list2.list', 'r')
    files2 = [f.strip() for f in fin.readlines()]
    fin.close()

    index = 64
    filename1 = "covers32k/" + files1[index] + ".mp3"
    filename2 = "covers32k/" + files2[index] + ".mp3"
    fileprefix = "Covers80_%i"%index

    artist1 = getArtistName(files1[index])
    artist2 = getArtistName(files2[index])
    songName = getSongName(files1[index])

    #filename1 = 'MIREX_CSIBSF/GotToGiveItUp.mp3'
    #filename2 = 'MIREX_CSIBSF/BlurredLines.mp3'
    #fileprefix = "BlurredLines"

    #FeatureParams = {'DPixels':200, 'NCurv':400, 'NJump':400, 'NTors':400, 'D2Samples':50, 'CurvSigma':20, 'D2Samples':40, 'MFCCSamplesPerBlock':200, 'GeodesicDelta':10, 'NGeodesic':400, 'lifterexp':0.6, 'MFCCBeatsPerBlock':12, 'ChromaBeatsPerBlock':20, 'ChromasPerBlock':40}
    #FeatureParams = {'ChromaBeatsPerBlock':20, 'ChromasPerBlock':40, 'DPixels':200, 'MFCCBeatsPerBlock':20}

    CurvSigmas = [10, 60]
    FeatureParams = {'MFCCBeatsPerBlock':20, 'MFCCSamplesPerBlock':200, 'DPixels':50, 'ChromaBeatsPerBlock':20, 'ChromasPerBlock':40}

    CSMTypes = {'MFCCs':'Euclidean', 'SSMs':'Euclidean', 'SSMsDiffusion':'Euclidean', 'Geodesics':'Euclidean', 'Jumps':'Euclidean', 'Curvs':'Euclidean', 'Tors':'Euclidean', 'CurvsSS':'Euclidean', 'TorsSS':'Euclidean', 'D2s':'EMD1D', 'Chromas':'CosineOTI'}
    for sigma in CurvSigmas:
        CSMTypes['Jumps%g'%sigma] = 'Euclidean'
        CSMTypes['Curvs%g'%sigma] = 'Euclidean'
        CSMTypes['Tors%g'%sigma] = 'Euclidean'

    compareTwoSongsJSON(filename1, TempoBias1, filename2, TempoBias2, hopSize, FeatureParams, CSMTypes, Kappa, "%s.json"%fileprefix, artist1, artist2)
