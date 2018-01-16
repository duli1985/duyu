#!user/bin/env Python
# -*- coding: utf-8 -*-

import requests
import paramiko
from config import config
import random
import time

# 交易执行状态：1-成功、2-失败、4-非法交易、9-处理中，为通联返回结果
RUN_RES_SUCCESS = '1'
RUN_RES_FAILURE = '2'
RUN_RES_INVALID = '4'
RUN_RES_HANDLING = '9'

def get_remote_sftp_client(hostname, port, username, password):
    #服务器信息，主机名（IP），端口号，用户名及密码
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password, compress=True)
    sftp_client = client.open_sftp()
    return sftp_client

def parse_price_to_point2f(price):
    #转换价格，保留两位小数点，比如8转换为8.00
    result = '0.00'
    try:
        result = float(price)
    except ValueError:
        print ("parse (%s) failed, return 0.00" % price)
        return result
    else:
        return format(result, '.2f')


def read_remote_file_D(upload_file_D, isLog=True):
    """远程读文件，返回title和lines"""
    ouput_title = [] #用文本数组，用'|'合并
    ouput_lines = []
    title_segments = []
    #这三个列表存目标文件的值，要放在for循环之前

    for line in upload_file_D:
        if line.startswith('TX'):
            # 交易数据
            # 交易类型|交易发起日期时间|交易流水号|基金代码|交易金额|银行代码|银行卡号|证件类型|证件号码|通联会员号
            # TX41|20180104113653|FB20171230192932BBO119001|020031|10000|03040000|6230209874563882|1|441402199202245603|201711221725306040


            segs = line.strip().split('|')
            #这是需要的字段
            seg0_type, seg2_instOrderNo, seg4_mount, seg5_bankCode, seg6_cardId, seg9_TLmemberId= segs[0], segs[2], segs[4], segs[5], segs[6], segs[9]

            # 构造目标文件的行
            # 交易数据
            # 交易类型|基金销售机构交易流水号|交易金额|银行代码|银行卡号|通联交易流水号|交易执行时间|交易执行状态
            # TX41 | FB20171230192932BBO119001 | 10000 | 03040000 | 6230209874563882 | 201711221725306040 | null | 9
            result_line_list = []
            result_line_list.append(seg0_type)
            result_line_list.append(seg2_instOrderNo)
            result_line_list.append(seg4_mount)
            result_line_list.append(seg5_bankCode)
            result_line_list.append(seg6_cardId)
            result_line_list.append(seg9_TLmemberId)
            result_line_list.append('null') #交易执行时间 设为null
            result_line_list.append(RUN_RES_SUCCESS) #每次运行，需要手工输入执行结果状态

            result_line_str = '|'.join(result_line_list)
            ouput_lines.append(result_line_str)

        else:
            # 文件头
            # 基金销售机构号|发起日期|批次号|总金额|总笔数
            # 100000087010000|20180108|2018010817520721|10000.0|1
            title_segments = line.strip().split('|')

    # 构造文件头
    # 基金销售机构号|发起日期|批次号|成功总金额|成功总笔数|失败总金额|失败总笔数|非法交易总金额|非法交易总笔数
    # 100000087010000 | 20180108000000 | 100000087010000_D2018010817520721_20180108000000 | 0.00 | 0 | 0.00 | 0 | 0.00 | 0
    ouput_title.append(title_segments[0]) #基金销售机构号
    ouput_title.append(title_segments[1]+'000000')
    ouput_title.append('{0}+D{1}+{2}000000'.format(title_segments[0], title_segments[2], title_segments[1]))
    # 其中{0} {1} {2}的三个参数占位符号，用后面format方法的三个参数生成一个字符串
    # 最后生成100000087010000_D2017122611453810_20171226000000

    #后面6个字段代表处理结果: 0.00 | 0 | 0.00 | 0 | 0.00 | 0
    #需手工输入处理结果，非必填
    ouput_title.append('0.00') #成功总金额
    ouput_title.append('0') #成功总笔数
    ouput_title.append('0.00') #失败总金额
    ouput_title.append('0') #失败总笔数
    ouput_title.append('0.00') #非法交易总金额
    ouput_title.append('0') #非法交易总笔数

    ouput_title_str = '|'.join(ouput_title)

    if isLog:
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


def read_remote_file_O(upload_file_O, isLog=True):
    #读O文件，返回title和lines
    ouput_title = []
    ouput_lines = []
    title_segments = []

    for line in upload_file_O:
        # O文件的源文件中，没有头文件
        # 交易数据
        # HT20171212103329129||201711201829523373|0|5|03040000|1|6230209874563882|13900005739|156|700|0|0|01|HQB|700|000709|20171212|HT20171212103329128|100000087010000||||
        # HT20171212103329129|20171212131242159696||201711201829523373|0|5|03040000|1|6230209874563882|13900005739|156|700.00|0.00|0||HQB|700.00|||HT20171212103329128|100000087010000||||20171212|0000|交易成功|
        if 'HT' in line:
            segs = line.strip().split('|')
            rdm = ''.join(random.choice('0123456789') for x in range(12))
            print rdm

            #构造目标文件交易数据
            result_line_list = []
            result_line_list.append(segs[0]) #HT20171212103329129
            result_line_list.append(segs[17] + rdm) #20171212131242159696
            result_line_list.append('null')
            result_line_list.append(segs[2]) #201711201829523373
            result_line_list.append(segs[3]) #0
            result_line_list.append(segs[4]) #5
            result_line_list.append(segs[5]) #03040000
            result_line_list.append(segs[6]) #1
            result_line_list.append(segs[7]) #6230209874563882
            result_line_list.append(segs[8]) #13900005739
            result_line_list.append(segs[9]) #156
            result_line_list.append(parse_price_to_point2f(segs[10])) #700.00
            result_line_list.append(segs[11]) #0
            result_line_list.append(segs[12]) #0
            result_line_list.append('null') #空
            result_line_list.append(segs[14]) #HQB
            result_line_list.append(parse_price_to_point2f(segs[15])) #700.00
            result_line_list.append('null') #空
            result_line_list.append('null')  # 空
            result_line_list.append(segs[18]) #HT20171212103329128
            result_line_list.append(segs[19]) #100000087010000
            result_line_list.append('null') #空
            result_line_list.append('null') #空
            result_line_list.append('null') #空
            result_line_list.append(segs[17]) #20171212
            result_line_list.append('0000') #0000
            result_line_list.append(u'交易成功') #交易成功

        #构造目标文件交易数据
            result_line_dir = '|'.join(result_line_list)
            ouput_lines.append(result_line_dir)
        # else:
    #文件头
    #0000|GW27L7/ODfmj2xjIcC3UStc+RMzto02EWXihbPzYe6di0Vu7xP3haCikdayam5V45AYHGh6dKf2zkTaisoBJ9lwDzqvKhIF5qkKTCwTV2RI0HNlYDHmcAIT8nwxLKeqyxlJq90TaP0+hXEZeCUP76fjNQlXG/u0VMbu8FOIzaAY=
    #         title_segments = line.strip().split('|')
    #
    # #构造文件头
    # ouput_title.append(title_segments[0])
    # ouput_title.append(title_segments[1])

    # 构造文件头
    ouput_title.append('0000')
    ouput_title.append(u'GW27L7/ODfmj2xjIcC3UStc+RMzto02EWXihbPzYe6di0Vu7xP3haCikdayam5V45AYHGh6dKf2zkTaisoBJ9lwDzqvKhIF5qkKTCwTV2RI0HNlYDHmcAIT8nwxLKeqyxlJq90TaP0+hXEZeCUP76fjNQlXG/u0VMbu8FOIzaAY=')
    ouput_title_dir = '|'.join(ouput_title)

    if isLog:
        print ouput_title_dir
        print ouput_lines
    return [ouput_title_dir] + ouput_lines


def write_file_with_lines(filename, lines_list):
    #把lines_list写入文件filename
    for line in lines_list:
        filename.write(line)
        filename.write('\n')



###########################################################################
##把功能全部写成def方法，放到前面。 下面是具体调用
###########################################################################
sftp_client = get_remote_sftp_client(hostname=config.file_interfaceHost,
                                     port=config.file_interfacePort,
                                     username=config.file_userName,
                                     password=config.file_pwd)

remote_path = '/opt/file/fund-gw/share-dir/export/settle/fundout/generate/'
the_day = '20180108' #手动输入日期

#选择文件
def choose_file_func(one_file_with_path, file_type, func):
    print "The file type is:", file_type
    print "handle it with this type (press any key to continue), or choose the other type: {'D': D, 'O': O, 'E': E}"
    choose = raw_input()
    #按照文件类型DEO不同，选择不同的执行方法
    if choose == 'D':
        print "You choose the D type"
        file_type = 'D'
        func = read_remote_file_D
    elif choose == 'E':
        print "You choose the E type"
        file_type = 'E'
        func = read_remote_file_E
    elif choose == 'O':
        print "You choose the O type"
        file_type = 'O'
        func = read_remote_file_O
    else:
        print "handle it with this type of parameter: %s" % file_type

    all_lines = []
    # print one_file_with_path, "is in process..."

    all_lines = func(one_file_with_path)
    return all_lines
    # try:
    #     all_lines = func(one_file_with_path)
    # except Exception as e:
    #     print e
    #     #处理文件出错的话，将错误原样打印出来
    # finally:
    #     return all_lines

def main(sftp_client, remote_path_add_the_day):
    the_day_remote_dirs = sftp_client.listdir(remote_path_add_the_day)
    dirs_dicts = {}
    #列出目录下所有的gbk文件，并生成一个以序号为主键的dict
    for no, one_file in enumerate(the_day_remote_dirs):
        if one_file.endswith('gbk.txt'):
            print no, one_file
            dirs_dicts[str(no)] = one_file

    print "choose your file:"
    file_no = raw_input()
    one_file = dirs_dicts[file_no]
    upload_file = sftp_client.open(remote_path_add_the_day + '/' + one_file, 'r')

    all_lines = []
    print one_file, "will be added to process"
    #按照EDO文件的不同，选择不同的执行方法
    #ED文件回执文件以back.txt结尾，O文件回执文件以RBP.txt结尾
    if 'O' in one_file:
        all_lines = choose_file_func(upload_file, 'O', read_remote_file_O)
        downLoad_file = sftp_client.open(remote_path_add_the_day + '/' + one_file.replace('BP_gbk' , 'RBP') , 'w')
        write_file_with_lines(downLoad_file , all_lines)
    elif 'D' in one_file:
        all_lines = choose_file_func(upload_file, 'D', read_remote_file_D)
        downLoad_file = sftp_client.open(remote_path_add_the_day + '/' + one_file.replace('gbk' , 'back') , 'w')
        write_file_with_lines(downLoad_file , all_lines)
    elif 'E' in one_file:
        all_lines = choose_file_func(upload_file, 'E', read_remote_file_E)
        downLoad_file = sftp_client.open(remote_path_add_the_day + '/' + one_file.replace('gbk' , 'back') , 'w')
        write_file_with_lines(downLoad_file , all_lines)
    else:
        print "Can't recognize your file"

    # #ED文件回执文件以back.txt结尾，O文件回执文件以RBP.txt结尾
    # downLoad_file = sftp_client.open(remote_path_add_the_day + '/' + one_file.replace('gbk','back'), 'w')
    # write_file_with_lines(downLoad_file, all_lines)

main(sftp_client, remote_path + the_day)