#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
证件管理系统
用于管理员工安全类证件的有效期和提醒功能
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class CertificateManager:
    """
    证件管理类
    负责处理证件的读取、检查和提醒功能
    """
    
    def __init__(self, data_file='data/certificates.csv'):
        """
        初始化证件管理器
        
        Args:
            data_file (str): 证件数据文件路径
        """
        self.data_file = data_file
        self.webhook_url = os.getenv('WEBHOOK_URL')
        
    def load_certificates(self):
        """
        加载证件数据
        
        Returns:
            pd.DataFrame: 证件数据DataFrame
        """
        try:
            return pd.read_csv(self.data_file)
        except FileNotFoundError:
            # 如果文件不存在，创建示例数据结构
            df = pd.DataFrame(columns=[
                'employee_id', 'employee_name', 'certificate_type',
                'certificate_number', 'issue_date', 'expiry_date',
                'check_date', 'check_interval_months'
            ])
            df.to_csv(self.data_file, index=False)
            return df
    
    def check_expiring_certificates(self, days_threshold=30):
        """
        检查即将过期的证件
        
        Args:
            days_threshold (int): 提前提醒天数
            
        Returns:
            list: 需要提醒的证件列表
        """
        df = self.load_certificates()
        today = datetime.now()
        threshold_date = today + timedelta(days=days_threshold)
        
        expiring_certs = df[
            (pd.to_datetime(df['expiry_date']) <= threshold_date) |
            (pd.to_datetime(df['check_date']) <= threshold_date)
        ]
        
        return expiring_certs.to_dict('records')
    
    def send_reminder(self, certificates):
        """
        发送提醒消息
        
        Args:
            certificates (list): 需要提醒的证件列表
        """
        if not certificates:
            return
            
        message = "🔔 证件到期提醒\n\n"
        for cert in certificates:
            message += f"员工：{cert['employee_name']}\n"
            message += f"证件类型：{cert['certificate_type']}\n"
            message += f"证件编号：{cert['certificate_number']}\n"
            
            expiry_date = pd.to_datetime(cert['expiry_date'])
            check_date = pd.to_datetime(cert['check_date'])
            today = datetime.now()
            
            if expiry_date <= today + timedelta(days=30):
                message += f"⚠️ 证件将在 {expiry_date.strftime('%Y-%m-%d')} 到期\n"
            if check_date <= today + timedelta(days=30):
                message += f"⚠️ 证件需要在 {check_date.strftime('%Y-%m-%d')} 前年检\n"
            message += "\n"
        
        # 发送到企业微信群机器人
        if self.webhook_url:
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            try:
                response = requests.post(self.webhook_url, json=data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"发送提醒失败: {e}")

def main():
    """
    主函数
    """
    manager = CertificateManager()
    expiring_certs = manager.check_expiring_certificates()
    manager.send_reminder(expiring_certs)

if __name__ == "__main__":
    main() 