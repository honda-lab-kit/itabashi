from __future__ import division

import numpy as np
# import cupy as cp
import pandas as pd
import itertools
import math
import chainer
from chainer import initializers
import chainer.links as L
import chainer.functions as F
from chainer.dataset import concat_examples
from chainer.cuda import to_cpu
from chainer import training
from chainer import Variable
from chainer import optimizers
import copy
# import relu_1
import shape_ver2
import running
import calc

from itertools import chain,combinations


#包除積分で使用するIEネットワークのクラス
class IE(chainer.Chain):
    def __init__(self, args, ie_data, cov):#ネットワークの骨組み（エッジとかノードとか）をきめてエッジの初期値を設定するとこ
        super(IE, self).__init__()
        self.args = args
        self.ie_data = ie_data
        self.dtype = np.float32

        # 代数積を取得
        self.hh = calc.daisu(len(self.ie_data[0]), args)
        # 集合を作成し取得
        self.add = calc.add(self.args.add, len(self.ie_data[0]))   
        # 各点集合の長さ[9, 45, 129, ,,, 510, 511]
        self.set_sum = calc.set_sum(self.hh)
        print("===== hidden units =====", flush=True)
        print("{}".format(self.set_sum[-1]))

        # 初期値設定スタート
        if self.args.pre_shoki == 'soukan':
            if self.args.fmodel == "on":
                pass
            else:
                if args.shoki_opt == "max_min":#データの各変数の最大値、最小値を取得するところ
                    if self.args.gpu_id >= 0:
                        # max_data = cp.max(cp.array(ie_data), axis = 0)
                        # min_data = cp.min(cp.array(ie_data), axis = 0)
                        pass
                    else:
                        max_data = np.max(np.array(ie_data), axis = 0)
                        min_data = np.min(np.array(ie_data), axis = 0)
                elif args.shoki_opt == "var_mean":
                    max_data = []
                    min_data = []
                    if self.args.gpu_id >= 0:
                        # data.s = [i for i in eanmuratea(ie_data) if cp.mean(ie_data[:,num]) - 2 * cp.std(ie_data[:,num]) < i and i <= cp.mean(ie_data[:,num]) + 2 * cp.std(ie_data[:,num])]
                        # data.s = [i for i in eanmuratea(ie_data) if cp.mean(ie_data[:,num]) - 2 * cp.std(ie_data[:,num]) < i and i <= cp.mean(ie_data[:,num]) + 2 * cp.std(ie_data[:,num])]
                        for ip in range(len(ie_data[0])):
                            # data = cp.array([i[1] for i in enumerate(ie_data.T[ip]) if cp.mean(ie_data, axis = 0)[ip] - 2 * cp.std(ie_data, axis = 0)[ip]  < i[1] and i[1] <= cp.mean(ie_data, axis = 0)[ip] + 2 * cp.mean(ie_data, axis = 0)[ip]])
                            # max_data.append(cp.max(data))
                            # min_data.append(cp.min(data))
                            pass
                    else:
                        for ip in range(len(len(ie_data[0]))):
                            data = np.array([i[1] for i in enumerate(ie_data.T[ip]) if np.mean(ie_data, axis = 0)[ip] - 2 * np.std(ie_data, axis = 0)[ip]  < i[1] and i[1] <= np.mean(ie_data, axis = 0)[ip] + 2 * np.mean(ie_data, axis = 0)[ip]])
                            max_data.append(np.max(data))
                            min_data.append(np.min(data))

                # 入力層ー中間層の W の初期値取得
                a = []
                b = []
                if self.args.initi == 'on':#初期値を手動設定する時
                    a.append(0.4)
                    a.append(6)
                    a.append(-0.08)
                    a.append(80)
                    b.append(-3.4)
                    b.append(-6)
                    b.append(3.4)
                    b.append(-3.4)
                else:#初期値を自動設定する時
                    for num in range(len(ie_data[0])):
                        # 相関係数による判別
                        if cov[num] > 0:
                            a.append(6 / (max_data[num] - min_data[num]))
                            b.append(-6* (min_data[num] + max_data[num]) / (2 * (max_data[num] - min_data[num])))
                        else:
                            a.append(-6 / (max_data[num] - min_data[num]))
                            b.append(6* (min_data[num] + max_data[num]) / (2 * (max_data[num] - min_data[num])))
                # if self.args.fmodel == "random":
                #     pass
                # elif self.args.fmodel == "init":
                #     for num in range(len(ie_data[0])):
                #         exec("self.fa"+ str(num + 1) + " = L.Linear(1, 1000, initialW=submodel.fc1.W.array[:, "+ str(num) +", np.newaxis], initial_bias=submodel.fc1.b.array)")  
                #         exec("self.fb"+ str(num + 1) + " = L.Linear(1000, 1, initialW=submodel.fc3.W.array[:, "+ str(num) +", np.newaxis], initial_bias=submodel.fc3.b.array)") 
                # else:
                #初期値の入力を行っていく
                with self.init_scope():
                    for num in range(len(ie_data[0])):
                        if self.args.gpu_id >= 0:
                            exec("self.l" + str(num + 1) + "= L.Linear(1, 1, initialW=cp.asnumpy(a[" + str(num) + "]), initial_bias=cp.asnumpy(b[" + str(num) + "]))")
                            exec("self.l"+str(num + 1)+".to_gpu(self.args.gpu_id)")
                        else:
                            exec("self.l" + str(num + 1) + "= L.Linear(1, 1, initialW=a[" + str(num) + "], initial_bias=b[" + str(num) + "])")

        elif(self.args.pre_shoki == 'random'):#初期値をランダムにする時
            with self.init_scope():
                for num in range(len(ie_data[0])):
                    exec("self.l" + str(num + 1) + "= L.Linear(1, 1)")
                self.lt = L.Linear(self.add, args.out)
                # self.la = L.Linear(1, 1, nobias=True) #バイアスなし、パラメータのためのもの

        elif(self.args.pre_shoki == 'units'):
            with self.init_scope():
                #前半の層のユニットを増やしたもの
                for num in range(len(ie_data[0])):
                    exec("self.fa"+ str(num + 1) + " = L.Linear(1, 1000)")  
                    exec("self.fb"+ str(num + 1) + " = L.Linear(1000, 1)") 
        else:
            print('error:前準備部分でpre_shokiの設定ミス')
        with self.init_scope():
            # 中間層ー出力層の初期値取得
            siki = calc.siki(self.add, len(self.ie_data[0]))
            # 初期値確保
            m = initializers.Constant(np.array(siki).T)
            m0 = initializers.Constant(np.array([0]))

            #tnormのパラメータの初期値取得
            if self.args.tnorm == "duboa" or self.args.tnorm == "dombi":
                ramda_init = initializers.Constant(np.full((1, self.add - len(ie_data[0])), 0.5))
                self.ramda = L.Linear(self.add - len(ie_data[0]), 1, initialW=ramda_init, nobias=True)

            self.lt = L.Linear(self.add, args.out, initialW=m, initial_bias=m0)
            if self.args.gpu_id >= 0:
                    self.lt.to_gpu(self.args.gpu_id)

    def __call__(self, x, tnorm = "daisu"):#関数が呼び出されるたびに実行される処理xのとなりにsubmodel
        for num in range(len(self.ie_data[0])):#xにバッチサイズごとのデータを入れていく
            exec("x" + str(num + 1) + "= x[:, " + str(num) + "]") 

        # for num in range(len(self.ie_data[0])):#xにバッチサイズごとのデータを入れていく
        #     exec('x' + str(num + 1) + '= np.ravel(submodel(np.insert(np.zeros([x.shape[0],x.shape[1]-1], dtype = "float32"), [' + str(num) + '], x[:,' + str(num) + '].reshape(-1, 1), axis = 1)).array)') 

        # 活性化関数の指定とパイプを通す
        #相関係数から決める場合
        if self.args.pre_shoki == "units":
            for num in range(len(self.ie_data[0])):#一個の変数のときのやつをhの最初に入れている。
                exec("h" + str(num + 1) + "= F.sigmoid(self.fb" + str(num + 1) + "(self.fa" + str(num + 1) + "(x" + str(num + 1) + ".reshape(1, len(x)).T)))")
        else:
            for num in range(len(self.ie_data[0])):#一個の変数のときのやつをhの最初に入れている。
                exec("h" + str(num + 1) + "= F.sigmoid(self.l" + str(num + 1) + "(x" + str(num + 1) + ".reshape(1, len(x)).T))")

        box = [] #各包除積分ネットワークの入力の値2^n-1を入れる入れ物
        if tnorm == "daisu":#tnormの選択と計算を行う。
            for length in range(1, self.add +1):
                for num in range(len(self.hh[length])):
                    if num == 0:
                        exec("h = h" + str(self.hh[length][num]))#最初にhに入れる変数をhにいれる。例h = h1
                    else:
                        exec("h *= h" + str(self.hh[length][num]))#今までの計算結果にtnormでさらに加えて演算する　例h1*h2のとき　h=h1して次にここで h *= h2としてh がh1*h2となるようにする。
                if length != 0:
                    exec("box.append(h)")
        elif tnorm == "ronri":
            for length in range(1, self.add +1):
                for num in range(len(self.hh[length])):
                    if num == 0:
                        exec("h = h" + str(self.hh[length][num]))
                    else:
                        exec("h = np.hstack([h.data,h" + str(self.hh[length][num]) + ".data])")#ｈにバッチサイズごとの変数の値を連結していく例(ｈ１、ｈ２,...)
                if length != 0 and num ==0:
                    exec("box.append(h)")#１変数の場合はそのままboxに入れる
                else:
                    exec("h = Variable(np.array([np.amin(h,axis=1)]).T)")#連結しておいた値を行ごとにminをとってバッチサイズ行1列の形にする
                    exec("box.append(h)")#各バッチサイズで最も小さい値をboxにいれる
        elif tnorm == "dombi":#調整中
            for length in range(1, self.add +1):
                for num in range(len(self.hh[length])):
                    if num == 0:
                        exec("h = h" + str(self.hh[length][num]))
                    else:
                        exec("h = 1/(1+((1/h-1)**self.ramda.W[0][" + str(length - len(x[0]) - 1) + "] + (1/h" + str(self.hh[length][num]) + " - 1)**self.ramda.W[0][" + str(length - len(x[0]) - 1) 
                        + "])**-self.ramda.W[0][" + str(length - len(x[0]) - 1) + "])")
                        #exec("h = (0**h)**h" + str((self.hh[length][num])))
                if length != 0:
                    exec("box.append(h)")
        elif tnorm == "duboa":
           for length in range(1, self.add +1):
                for num in range(len(self.hh[length])):
                    if num == 0:
                        exec("h = h" + str(self.hh[length][num]))
                    else:#duboa_pradeの演算をバッチサイズごとに行う
                        exec("h = h*h" + str(self.hh[length][num]) + "*(Variable(np.array([np.amax(np.hstack([h.data,h" + str(self.hh[length][num]) 
                        + ".data, np.full((len(h),1),self.ramda.W[0][" + str(length - len(x[0]) - 1) + "].data)]),axis=1)]).T))**-1")
                if length != 0:
                    exec("box.append(h)")
        else:
            print("tnorm選択して")
        

        ht = F.hstack(box)#htに形をととのえたやつを代入
        return self.lt(ht)#ここでようやくltの各重みに入力となる値を入れて出力を返す