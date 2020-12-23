# -*- coding: utf-8; -*-

# import file
import mlp
import submlp
# import training
import saving_data
import ie_11_14
import calc
import running

# library
import datetime
import Hyperreal
import os
import argparse
import random
import pickle
import sys
import copy
import math
import pandas as pd
import numpy as np
import csv
import time
import pylab
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import ClusterCentroids, RandomUnderSampler

# chainer 
import chainer
from chainer.datasets import split_dataset_random, get_cross_validation_datasets_random
from chainer import iterators, optimizers, serializers, cuda
from chainer.optimizer_hooks import WeightDecay, Lasso

def main():

	# read config
	parser = argparse.ArgumentParser()
	dtn = datetime.datetime.now()
	# モデルをリストに入れる
	model_list = []
	shape_list = []
	# よく変更するパラメータ
	parser.add_argument('--epoch', type=int, default=10, help='epoch for each generation')
	parser.add_argument('--mlp_units', type=int, default=21, help='mlpの中間層のユニット数')
	parser.add_argument('--subepoch', type=int, default=2000, help='前の学習をさせたかった')
	parser.add_argument('--loss_epoch', type=int, default=10000, help='テストデータに対する減少傾向が確認されてからの打ち切りまでの学習回数')
	parser.add_argument('--null_impcount', type=int, default=1, help='null_importanceを見るための比較回数')
	parser.add_argument('--add', type=int, default=6, help='add: 1 or 2 or 3 or 9(all)')
	parser.add_argument('--data_model', type=str, default='Titanic_train_3pop', help='_3_3_pool_1_mnist_2class：CSVの入力ファイル指名')
	parser.add_argument('--lossf', type=str, default='mse_sig', help='dataset: entoropy or mean_squrd：損失誤差関数')
	parser.add_argument('--day', type=str, default=str(dtn.month)+str(dtn.day)+str(dtn.hour)+str(dtn.minute), help='data_file_name：日付指定 例str(dtn.month)+str(dtn.day)+str(dtn.hour)+str(dtn.minute)')
	parser.add_argument('--Titanic',type=str, default='on', help='on or off：タイタニックデータ用')
	parser.add_argument('--acc_info',type=str, default='on', help='on or off：正答率や再現性とかの情報出力するか否か')
	parser.add_argument('--tnorm', type=str, default='daisu', help='daisu or ronri or dombi or duboa')#tnormの型決め
	parser.add_argument('--fmodel', type=str, default='random', help='最初の層を多数のユニットを使って学習させる。ランダムならrandom、初期値を学習させて決めるならinit')
	parser.add_argument('--save_data', type=str, default='save', help='save or not')
	parser.add_argument('--pre_ie', type=str, default='pre_mlp', help='premlp or precor')
	parser.add_argument('--permuimp', type=str, default='off', help='premlp or precor')
	parser.add_argument('--boot', type=int, default='1000', help='ブートストラップ法で目的変数のデータ数を合わせる。その時の抽出するデータ数。1ならただの交差検証。目的変数の形は正の整数0~')
	parser.add_argument('--pre_shoki', type=str,default='soukan',help='soukan:相関から初期値を決める,random:初期値をランダムに決める,units:適当なユニット数で学習')

	#初期値手動で変えるとき使用
	parser.add_argument('--initi',type=str, default='off', help='on or off')

	# k分割交差検証するときはk>1の整数。しないときはk=1にしてください。お願いします。あとk=1にしたらtrain_rateは0以上にしないとエラーが起きる
	parser.add_argument('--train_rate',type=float ,default=1, help='0~1の間trainの割合を決める.1ならテストなし')
	parser.add_argument('--k', type=int, default=1, help='k分割交差検証のkの値。1だと分割せずそれ以上の整数値だと分割する')
	parser.add_argument('--sampling', type=str, default='Cluster', help='サンプリングの手法を選択')
	parser.add_argument('--k_test', type=int, default=0, help='k分割交差検証のtestデータをさらに作るなら１にして')

	# データのディレクトリの場所のパラメータ
	parser.add_argument('--directri', type=str, default='Titanic', help='ディレクトリを指定')

	# 正規化項用の引数
	parser.add_argument('--norm', type=str, default='lt', help='l1 or l2 or lt')
	parser.add_argument('--lr', type=float, default=0.001, help='learning rate')
	parser.add_argument('--l_lr', type=float, default=0.001, help='learning rate')

	# あんま変更しないパラメータ
	parser.add_argument('--gpu_id', type=int, default=-1)
	parser.add_argument('--out', type=int, default=1, help='units_out in each layer')
	parser.add_argument('--batch_size', type=int, default=200)
	parser.add_argument('--func', type=str, default='relu_1', help='dataset: sigmoid or relu_1')
	parser.add_argument('--model', type=str, default='ie', help='dataset: mlp or cnn')
	parser.add_argument('--opt', type=str, default='adam', help='dataset: sgd or adam')
	parser.add_argument('--shoki_opt', type=str, default='max_min', help='')
	parser.add_argument('--train_number', type=int, default=2, help='learning rate')
	parser.add_argument('--limit', type=float, default=1, help='limit_train_data')
	parser.add_argument('--mono', type=float, default=0, help='monotony value')
	parser.add_argument('--unit', type=float, default=800, help='learning rate')
	parser.add_argument('--data', type=str, default='mnist', help='datSaset: car or mnist')
	parser.add_argument('--not_monotony', action='store_true',help='つけたら単調性なし')
	parser.add_argument('--debug', action='store_true')
	parser.add_argument('--not_shape_model', action='store_true')	
	parser.add_argument('--w_name', type=str, default='w_default', help='data_file_name')
	
	# parser.add_argument('--data_folder', type=str, default='mnist', help='mnist or titanic or ')
	parser.add_argument('--data_shape_model', type=str, default='chainer_7_7_mnist_2class', help='data_model')
	parser.add_argument('--train_name', type=str, default='Y', help='')

	args = parser.parse_args()

	# read data
	print("===== read data =====", flush=True)
	print()
	print("===== gpu =====", flush=True)
	print("{}".format(args.gpu_id))
	print("===== add =====", flush=True)
	print("{}".format(args.add))
	
	# with open('./data/Titanic/{}.pkl'.format('Titanic_test_1_class'), mode="rb") as f:
	# 	Rtest = pickle.load(f)
	#データの読み込み
	
	dataset = np.genfromtxt("./data/{}/{}.csv".format(args.directri, args.data_model), delimiter=",", filling_values=0).astype(np.float32)
	
	valuesize = dataset.shape[1]
	#Y = (dataset[1:dataset.shape[0], 0]).astype(np.int32)
	Y = (dataset[0:dataset.shape[0], 0])
	X1 = dataset[0:dataset.shape[0], 1:valuesize]

	#クラスタリングの選択
	if args.sampling == 'ClusterCentroids':
		X1,Y = ClusterCentroids(sampling_strategy=1 ,random_state=0).fit_resample(X1,Y) #sampling_strategy=low_sample/lot_sample
	elif args.sampling == 'SMOTE':
		X1,Y = SMOTE(random_state=0).fit_resample(X1, Y)
	elif args.sampling == 'RandomUnderSampler':
		X1,Y = RandomUnderSampler(random_state=0).fit_resample(X1, Y)
	else:
		print('サンプリングなし')
		pass
	
	null_importance = []

	for rnum in range(args.null_impcount):

		if rnum == 0:
			Y1 = Y
			pass
		else:
			Y1 = np.random.permutation(Y)
			pass

		#Xにチェイナーのタプル型を設定
		X = chainer.datasets.TupleDataset(X1, Y1)
		
		#k分割交差検証を行うとき、学習データとテストデータに分けるときに使用
		if args.k == 1 and args.train_rate == 1 :#交差なし、全データで学習
			train = X
			test  = X
		elif args.k == 1:#交差なし、学習比率調整
			trainsize = int(X._length*args.train_rate)
			train, test = split_dataset_random(X, trainsize)
		elif rnum == 0:#ｋ分割交差かブートストラップ法によるデータ分割
			cross_dataset = calc.cross_valid_custum(dataset, args.k + args.k_test, args.boot)
		elif rnum != 0:#交差あり、null_impourtance計算する
			trainsize = int(X._length*(1-1/args.k))
			train, test = split_dataset_random(X, trainsize)
		else:
			print("データ準備エラー")

		score_sum, precision_sum, recall_sum, f1_sum, AUC_sum = 0,0,0,0,0

		#本学習がすんだらnull_importance学習するために下のforループは1回にする
		if rnum == 0:
			num_k = args.k
		else:
			num_k = 1

		for i in range(num_k):
			print("===== start train =====", flush=True)#ここから学習開始
			print("number : 0 _ " + str(args.train_number-1+1) + "")

			if args.k > 1 and rnum == 0:
				train, test = cross_dataset[i]
			else:
				pass

			"""
			データの注意点
			データの中身：train[0~8]
			インデックス　：[0 ,  1,   2,  , ..., 8  ] 
			中身ののデータ：[0_1, 0_2, 0_3,  ..., 0_9]
			"""

			# データ用意*データ数少なくしたいときに使う
			if not args.debug:
				train_iter = iterators.SerialIterator(train, args.batch_size, shuffle=False)
				test_iter = iterators.SerialIterator(test, len(test), shuffle = False)
			# デバッグ用データ用意
			else: 
				train_iter = iterators.SerialIterator(train[1:500], args.batch_size, shuffle=None)
				test_iter = iterators.SerialIterator(test[1:500], len(test))
			
			# define alg　更新式の選択
			optimizer = chainer.optimizers
			define_opt = args.opt
			if define_opt == "sgd":
				optimizer = optimizer.SGD(lr=args.lr)
			elif define_opt == "adam":
				optimizer = optimizer.Adam(alpha=args.lr)

			# define model　通常のニューラルネットワークにするかIEネットワークにするかを選択
			define_model = args.model
			if define_model == "mlp":
				model = mlp.MLP(args)
			elif define_model == "ie":
				ie_data, cov = calc.ie_data_and_cov(train)
				if args.fmodel == "init":
					subelapsed_time = []
					substart = time.time()
					submodel = submlp.subMLP(args)
					optimizer.setup(submodel)
					# substart time
					subsummary = submodel.train_model(train_iter, test_iter, optimizer, subelapsed_time, substart, args)
					
				else:
					submodel = submlp.subMLP(args)
					optimizer.setup(submodel)
				model = ie_11_14.IE(args, train, cov)
				
			optimizer.setup(model)
			# for num in range(len(ie_data[0])):
			# 	exec("model.fa"+ str(num + 1) + ".disable_update()")  
			# 	exec("model.fb"+ str(num + 1) + ".disable_update()") 


			#GPUの時につかったり
			if args.gpu_id >= 0:
				gpu_device = args.gpu_id
				#chainer.cuda.get_device(args.gpu_id).use()
				model.to_gpu(gpu_device)
			
			
			# define norm　正則化項の情報を適用する
			calc.norm(model, args)

			print("===== om/off debug data =====", flush=True)
			print(len(train_iter.dataset))
			print("===== model name =====", flush=True)
			print(define_model)
			print("===== model func =====", flush=True)
			print(args.func)
			print("===== model opt =====", flush=True)
			print(args.opt)
			print("===== model lr =====", flush=True)
			print(args.lr)

			# start time
			elapsed_time = []
			start = time.time()

			# start train　ここでrunningfileのrun関数で学習を行う
			if args.model == "mlp":
				summary = model.train_model(train_iter, test_iter, optimizer, elapsed_time, start, args)
			elif args.model == "ie":
				summary = running.run(model, train_iter, test_iter, optimizer, elapsed_time, start, args)

			# 出力１かつ二値分類の場合使用すべし（AUCとか再現率を見たいとき）
			if args.out == 1:
				if args.acc_info == 'on':
					try:
						score, precision, recall, f1, AUC = calc.accuracy(train._datasets[1],model(train._datasets[0]).array)
					except AttributeError:
						score, precision, recall, f1, AUC = calc.accuracy(test._dataset[test._order[test._start:test._start+test._size].tolist()][1],model(test._dataset[test._order[test._start:test._start+test._size].tolist()][0],args.tnorm).array)
				else:
					pass
			else:
				pass
			
			#k分割の精度の合計を作る
			if args.acc_info == 'on':
				score_sum += score
				precision_sum += precision
				recall_sum += recall
				f1_sum += f1
				AUC_sum += AUC
			else:
				pass
			model_list.append(model)

			if args.model == "ie":
				if summary[5] == args.epoch:
					summary[5] -= 1
				shape_list.append(summary[4][summary[5]])

			# saving result data
			if args.save_data == "save":
				if args.model == "ie" and rnum == 0:
					saving_data.saving_ie(summary, args, i+1)
				elif args.model =="mlp" and rnum == 0:
					saving_data.saving_mlp(summary, args, i+1)
			
		if args.model == "ie" and rnum == 0:
			print(np.round(np.array(shape_list), decimals=3))
			print('平均シャープレイ値',np.round(np.mean(np.array(shape_list),axis=0), decimals=4))
			print('平均重要度',np.round(np.mean(np.array(abs(np.array(shape_list))), axis=0), decimals=4))
		
		if args.k > 1:#labelが2値の場合に使用する
			if args.acc_info == "on":
				print()
				print('平均精度')
				print('精度:{:.3f}'.format(score_sum/args.k))
				print('適合率:{:.3f}'.format(precision_sum/args.k))
				print('再現率:{:.3f}'.format(recall_sum/args.k))
				print('f-1値:{:.3f}'.format(f1_sum/args.k))
				print("AUC_score:{:.3f}".format(AUC_sum/args.k))
			else:
				pass
		else:
			pass
		
		print("sampling_type:"+ args.sampling)
		#決定係数表示
		#赤池情報量表示
		mod_r2_sum = 0
		mod_ak_sum = 0
		if args.model == "ie" and rnum == 0:
			if args.train_rate == 1 and args.k > 1:
				mon = 0
				for mod in model_list:
					train, test = cross_dataset[mon]
					mod_r2_sum += calc.calc_r2(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf)
					mod_ak_sum += calc.calc_ak_mse(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf, valuesize)
						# train, test = cross_dataset[mon]
						# mod_r2_sum += calc.calc_r2(test._dataset[test._order[test._start:test._start+test._size].tolist()][1],mod(test._dataset[test._order[test._start:test._start+test._size].tolist()][0], args.tnorm).array)
						# mod_ak_sum += calc.calc_ak_mse(test._dataset[test._order[test._start:test._start+test._size].tolist()][1],mod(test._dataset[test._order[test._start:test._start+test._size].tolist()][0], args.tnorm).array, valuesize)
					mon += 1
			# elif args.train_rate == 1:
			# 	for mod in model_list:
			# 		mod_r2_sum += calc.calc_r2(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf)
			# 		mod_ak_sum += calc.calc_ak_mse(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf, valuesize)
			else:
				for mod in model_list:
					mod_r2_sum += calc.calc_r2(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf)
					mod_ak_sum += calc.calc_ak_mse(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf, valuesize)
					# mod_r2_sum += calc.calc_r2(test._dataset[test._order[test._start:test._start+test._size].tolist()][1],mod(test._dataset[test._order[test._start:test._start+test._size].tolist()][0], args.tnorm).array)
					# mod_ak_sum += calc.calc_ak_mse(test._dataset[test._order[test._start:test._start+test._size].tolist()][1],mod(test._dataset[test._order[test._start:test._start+test._size].tolist()][0], args.tnorm).array, valuesize)
			memo = mod_r2_sum/len(model_list)
			memo2 = mod_ak_sum/len(model_list)
			print("平均決定係数:{}".format(memo))
			print("平均赤池情報量規準:{}".format(memo2))
		elif args.model == "mlp":
			if args.train_rate == 1 and args.k > 1:
				mon = 0
				for mod in model_list:
					train, test = cross_dataset[mon]
					mod_r2_sum += calc.calc_r2(test._datasets[1],mod(test._datasets[0]).array, args.lossf)
					mod_ak_sum += calc.calc_ak_mse(test._datasets[1],mod(test._datasets[0]).array, args.lossf, valuesize)
			#elif args.train_rate == 1:
				# mod_r2_sum += calc.calc_r2(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf)
				# mod_ak_sum += calc.calc_ak_mse(test._datasets[1],mod(test._datasets[0], args.tnorm).array, args.lossf, valuesize)
				#print(calc.print_r2(test._datasets[1],model(test._datasets[0]).array, args.lossf))
			else:
				for mod in model_list:
					mod_r2_sum += calc.calc_r2(test._datasets[1],mod(test._datasets[0]).array, args.lossf)
					mod_ak_sum += calc.calc_ak_mse(test._datasets[1],mod(test._datasets[0]).array, args.lossf, valuesize)
				# npの形で入れるためこんな長くなってる
				#print(calc.print_r2(test._dataset[test._order[test._start:test._start+test._size].tolist()][1],model(test._dataset[test._order[test._start:test._start+test._size].tolist()][0]).array, args.lossf))
			memo = mod_r2_sum/len(model_list)
			memo2 = mod_ak_sum/len(model_list)
		else:
			pass


		# 検証データでデータを作る(タイタニック用)
		if(args.Titanic == 'on'):
			if dataset.shape[1] == 7:
				Rtest = np.genfromtxt("./data/Titanic/Titanic_test2_3pop.csv", delimiter=",", filling_values=0).astype(np.float32)
			elif dataset.shape[1] == 9:
				Rtest = np.genfromtxt("./data/Titanic/test_analys_data_v2.csv", delimiter=",", filling_values=0).astype(np.float32)
			elif valuesize == 10:
				Rtest = np.genfromtxt("./data/Titanic/Titanic_test2.csv", delimiter=",", filling_values=0).astype(np.float32)
			else:
				print('Titanic_data_error')
			Rtest = Rtest[1:]
			no = 0
			for mod in model_list:
				calc.craft_titanic(mod, args, Rtest, no)
				no += 1
			calc.craft_titanic_sum(model_list,args,Rtest)
		else:
			pass
		
		if args.model =="ie" and args.save_data == "save" and rnum == 0 and args.null_impcount != 1:
			shalist = np.zeros([test._size, X1.shape[1]], dtype = float)
			for i in range(X1.shape[1]):
				num =test._dataset[test._order[test._start:test._start+test._size].tolist()][0]
				num[:, i] = 0
				shalist[:, i] = model(num).array.reshape(-1, )
			shalist = np.insert(shalist, X1.shape[1], model.lt.b.array[0], axis=1)
			# 変数を除いた時の値+ バイアスの値＋出力の値で構成された行列をエクセルとして保存
			np.savetxt('./result/shapy/modeltest_shapy_{}_add{}.csv'.format(args.sampling, args.add), np.hstack((shalist, model(test._dataset[test._order[test._start:test._start+test._size].tolist()][0]).array)), delimiter = ',')
		else:
			pass

		if args.permuimp == "on":
			permutation_Importance = []
			target_num = test._dataset[test._order[test._start:test._start+test._size].tolist()][0]
			real_loss = np.sqrt(mean_squared_error(test._dataset[test._order[test._start:test._start+test._size].tolist()][1], model(target_num).array))
			for permu in range(X1.shape[1]):
				permu_mean = []
				for i in range(10):
					num = test._dataset[test._order[test._start:test._start+test._size].tolist()][0]
					np.random.shuffle(num[:, permu])
					permu_mean.append(real_loss - np.sqrt(mean_squared_error(test._dataset[test._order[test._start:test._start+test._size].tolist()][1], model(num).array)))
				permutation_Importance.append(sum(permu_mean)/len(permu_mean))
			print("permutation_Importance:{}".format(permutation_Importance))

		if rnum == 0:
			# real_importance
			null_importance.append(np.round(np.mean(np.array(shape_list),axis=0), decimals=10).tolist())
		else:
			#null_importance
			null_importance.append(summary[4][summary[5]])

	print("平均決定係数:{}".format(memo))
	print("平均赤池情報量規準:{}".format(memo2))

	#calc.show_units(model)

	if args.null_impcount == 1:
		pass
	else:
		value_list = calc.daisu(valuesize-1,args)[1:]
		null_importance.insert(0, value_list)
		for i in range(valuesize-1):	
			calc.display_null_importance(null_importance, i, args)
		null_importance = np.array(null_importance)[:, np.argsort(np.array(null_importance)[1])[::-1]].tolist()
		for i in range(10):	
			calc.display_null_importance(null_importance, i, args)
	





	



if __name__ == '__main__':
	main()