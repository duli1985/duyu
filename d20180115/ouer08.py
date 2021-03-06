#!/usr/bin/env python
# -*- coding: utf-8 -*-

from config import config
import paramiko
# import os
# import sys
# import re
# import requests


def get_remote_sftp_client(hostname, port, username, password)
    #服务器信息，主机名（IP地址）、端口号、用户名及密码
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password, compress=True)
    sftp_client = client.open_sftp()
    return sftp_client


def parse_price_to_point2f(price):
    """转换价格，保留2个小数点，比如8转换成8.00"""
    result = '0.00'
    try:
        result = float(price)
    except ValueError:
        print("parse (%s) failed, return 0.00" % price)
        return result
    else:
        return format(result, '.2f')


def read_remote_file_D(upload_file_D, is_log=True):
    """ 远程读文件， 返回title和lines  这个方法只用于处理D文件"""

    ouput_title = [] #用文本数组，最后用|合并
    ouput_lines = []
    title_segments = []
    # 这三个存目标值的，要放在for循环之前

    for line in upload_file_D:
        if line.startswith('TX'):
            # 详细条目
            # TX41|20171226093224|FB20171220213224BBO118514|BANK|50|03040000|6230209874563882|1|441402199202245603|201711221725306040
            # 交易类型，基金销售机构交易流水号，通联交易流水号
            segs = line.strip().split('|')
            # 这是需要的几个字段
            seg0_tx41, seg2_fb, seg4_money, seg5_bank, seg6_bankcard, seg9 = segs[0], segs[2], segs[4], segs[5], segs[6], segs[9]
            # 构造目标文件的行
            result_line_list = []
            result_line_list.append(seg0_tx41) 
            result_line_list.append(seg2_fb) 
            result_line_list.append(parse_price_to_point2f(seg4_money))
            result_line_list.append(seg5_bank) 
            result_line_list.append(seg6_bankcard) 
            result_line_list.append(seg9) 
            result_line_list.append('null') # 交易执行时间 设为null
            result_line_list.append('9') # 交易执行状态 1 2 4 9 应该是根据源文件的某些来判断吧，这个规则看你怎么实现

            result_line_str = '|'.join(result_line_list)
            ouput_lines.append(result_line_str)
        else:
            # 标题行
            title_segments = line.strip().split('|')

    # 构造标题行 
    # 100000087010000|20171226000000|100000087010000_D2017122611453810_20171226000000|0.00|0|0.00|0|0.00|0
    ouput_title.append(title_segments[0]) # 基金销售机构
    ouput_title.append(title_segments[1] + '000000')  # 20171226000000
    ouput_title.append('{0}_D{1}_{2}000000'.format(title_segments[0], title_segments[2], title_segments[1])) 
    # 其中{0} {1} {2}的三个参数占位符号，用后面format方法的三个参数生成一个字符串
    # 最后生成100000087010000_D2017122611453810_20171226000000

    # 后面的6个字段，你怎么处理 0.00|0|0.00|0|0.00|0
    ouput_title.append('0.00')
    ouput_title.append('0')
    ouput_title.append('0.00')
    ouput_title.append('0')
    ouput_title.append('0.00')
    ouput_title.append('0')

    ouput_title_str = '|'.join(ouput_title)

    if is_log:
        print ouput_title_str
        print ouput_lines

    return [ouput_title_str] + ouput_lines


def read_remote_file_E(upload_file_E, is_log=True):
    """ 读文件， 返回title和lines  这个方法只用于处理D文件"""

    ouput_title = [] #用文本数组，最后用|合并
    ouput_lines = []
    title_segments = []

    for line in upload_file_E:

        if 'HT' in line:
            # 源文件详细条目
            # 100000087010000|HT20171212103329126|20171212092638|01712102535BBO117271|20171212|FB201712102535BBO117271|5|HQB|8|03040000|6230200840165260|1|450226198809198811|201710111209142934|78110000|||||

            # 需要的几个字段是
            # HT20171212103329126|20171212092638|01712102535BBO117271|20171212|5|HQB|8.00|03040000|6230200840165260|20171212103044401663|78110000|20171212204845|1|

            segs = line.strip().split('|')
            # 这是需要的几个字段，我不单独取名字了，直接append
            result_line_list = []
            result_line_list.append(segs[1])  # HT20171212103329128
            result_line_list.append(segs[2])  # 20171212092638
            result_line_list.append(segs[3])  # 01712102535BBO117271
            result_line_list.append(segs[4])  # 20171212
            result_line_list.append(segs[6])  # 5
            result_line_list.append(segs[7])  # HQB
            result_line_list.append(parse_price_to_point2f(segs[8]))  # 8 转换成8.00
            result_line_list.append(segs[9])  # 03040000
            result_line_list.append(segs[10]) # 6230200840165260
            result_line_list.append(segs[13]) # 20171212103044401663  ==
            result_line_list.append(segs[14]) # 78110000
            result_line_list.append(segs[2])  # 20171212204845 目标文件的这个字段，源文件没有 我这边暂时用segs[2]代替 
            # result_line_list.append('null')   ## 或者像D那样 交易执行时间 设为null
            result_line_list.append('1')  # 交易执行状态 1 2 4 9 应该是根据源文件的某些来判断吧，这个规则看你怎么实现
            result_line_list.append('') 

            result_line_str = '|'.join(result_line_list)
            ouput_lines.append(result_line_str)
        else:
            # 标题行
            title_segments = line.strip().split('|')

    # 构造标题行 
    # 文件头：基金销售机构号|发起日期|批次号|转换成功总金额|转换成功总笔数|转换失败总金额|转换失败总笔数
    # 100000087010000|20171212103044|2017121210332925|15.00|2|0|0
    ouput_title.append(title_segments[0])
    ouput_title.append(title_segments[1] + '000000')  # 20171226000000
    ouput_title.append(title_segments[2])
    ouput_title.append(title_segments[3])
    ouput_title.append(title_segments[4])
    ouput_title.append('0')
    ouput_title.append('0')

    ouput_title_str = '|'.join(ouput_title)

    if is_log:
        print ouput_title_str
        print ouput_lines

    return ['|'.join(ouput_title)] + ouput_lines


def read_remote_file_O(upload_file_O, is_log=True):
    """ 远程读文件， 返回title和lines  这个方法只用于处理O文件"""
    # todo
    return ['O file is not supported']


def write_file_with_lines(filename, lines_list):
    # 把lines_list写入文件filename
    for line in lines_list:
        filename.write(line)
        filename.write('\n')



#################################################################
##    把功能全部写成def方法，放到之前。  这下面是具体调用      ##
#################################################################



sftp_client = get_remote_sftp_client(hostname=config.file_interfaceHost, 
                                     port=config.file_interfacePort, 
                                     username=config.file_userName, 
                                     password=config.file_pwd)

remote_path = "/opt/file/fund-gw/share-dir/export/settle/fundout/generate/"

the_day = '20180108' # 每次手动改这里吧


def _choose_file_func(one_file_with_path, file_type, func):
    """按照给定的文件类型，选择相应的处理方法；会询问一次，可以输入其他处理类型
    （也就是说，先默认按文件里的OED自动识别一个文件类型，但是也许不一定对，会询问一次）"""
    print "the file type is maybe: ", file_type
    print "handle it with this type (press any key to continue), or choose the other type: {'D': D, 'O': O, 'E': E}"
    choose = raw_input()
    # 按 DE文件的不同，选择不同的执行方法
    if choose == 'D':
        print "you choose the D type."
        file_type = 'D'
        func = read_remote_file_D
    elif choose == 'E':
        print "you choose the E type."
        file_type = 'E'
        func = read_remote_file_O
    elif choose == 'O':
        print "you choose the O type."
        file_type = 'O'
        func = read_remote_file_O
    else:
        print "handle it with this type of parameter: %s " % file_type

    all_lines = []
    # print one_file_with_path, "is in process..."
    try:
        all_lines = func(one_file_with_path)
    except Exception as e:
        print e
        # 处理文件可能出错，这边把错误 原样打出来。
    finally:
        return all_lines


def main(sftp_client, remote_path_add_the_day):
    """ the main function """

    # 这三种写法都可以
    # sftp_client.chdir(remote_path_add_the_day)
    # the_day_remote_dirs = sftp_client.listdir()
    the_day_remote_dirs = sftp_client.listdir(remote_path_add_the_day)
    # the_day_remote_dirs = sftp_client.listdir(remote_path_add_the_day + '/')

    dirs_dicts = {}
    # 列出该目录下所有gbk文件，并生成一个以序号为主键的dict
    for no, one_file in enumerate(the_day_remote_dirs):
        if one_file.endswith('gbk.txt'):
            print no, one_file
            dirs_dicts[str(no)] = one_file

    print "please choose your file: "
    file_no = raw_input()
    one_file = dirs_dicts[file_no]
    upload_file = sftp_client.open(remote_path_add_the_day + '/' + one_file, 'r')

    all_lines = []
    print one_file, " will be added to process..."
    # 按 ODE文件的不同，选择不同的执行方法
    if 'O' in one_file:
        all_lines = _choose_file_func(upload_file, 'O', read_remote_file_O)
    elif 'D' in one_file:
        all_lines = _choose_file_func(upload_file, 'D', read_remote_file_D)
    elif 'E' in one_file:  # E文件的处理方法还没写，可以先把这两行注释了
        all_lines = _choose_file_func(upload_file, 'E', read_remote_file_E)
    else:
        print "can not recognize your file."
    
    download_file = sftp_client.open(remote_path_add_the_day + '/' + one_file.replace('gbk', 'back'), 'w')
    write_file_with_lines(download_file, all_lines)



main(sftp_client, remote_path + the_day)