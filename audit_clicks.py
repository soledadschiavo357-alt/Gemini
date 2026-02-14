import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time

# ================= 配置区域 =================
# 1. 你的 Zone ID
ZONE_ID = "18f8b962404e1776d2763932dd77d5d0"

# 2. 你的新 Token (记得填进去!)
API_TOKEN = "FtJqU7byEUycHilz7afQEY7NKdsVyHOWucU41NLt" 

# ===========================================

def run_audit():
    print("🚀 V5 分片扫描版启动: 正在逐天拉取数据 (绕过24h限制)...")
    
    url = "https://api.cloudflare.com/client/v4/graphql"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 初始化总数据容器
    grand_total_visits = 0
    grand_cta_data = defaultdict(int)
    
    # 循环 7 次，查询过去 7 天，每天查一次
    for i in range(7):
        # 计算当天的开始和结束时间 (精确到天)
        # 例如: 今天是 13号。
        # i=0 -> start=12号, end=13号 (昨天)
        # i=1 -> start=11号, end=12号 (前天)
        end_date = datetime.now() - timedelta(days=i)
        start_date = datetime.now() - timedelta(days=i+1)
        
        str_start = start_date.strftime('%Y-%m-%d')
        str_end = end_date.strftime('%Y-%m-%d')
        
        print(f"   ⏳ 正在扫描第 {i+1} 天: {str_start} ...", end="", flush=True)

        # 针对每一天的查询 (确保时间跨度 <= 24小时)
        query = f"""
        query {{
          viewer {{
            zones(filter: {{zoneTag: "{ZONE_ID}"}}) {{
              httpRequestsAdaptiveGroups(
                limit: 2000,
                filter: {{
                  date_geq: "{str_start}",
                  date_lt: "{str_end}"
                }},
                orderBy: [count_DESC]
              ) {{
                dimensions {{
                  clientRequestPath
                }}
                count
              }}
            }}
          }}
        }}
        """

        try:
            response = requests.post(url, json={'query': query}, headers=headers)
            
            if response.status_code != 200:
                print(f" [失败: HTTP {response.status_code}]")
                continue

            result = response.json()
            
            # 错误检查
            if "errors" in result and result["errors"]:
                # 如果某一天没数据或报错，跳过
                print(f" [API提示: {result['errors'][0]['message']}]")
                continue

            data_zone = result["data"]["viewer"]["zones"]
            if not data_zone:
                print(" [无权限]")
                break
                
            raw_data = data_zone[0]["httpRequestsAdaptiveGroups"]
            
            # 累加当天数据
            daily_visits = 0
            for item in raw_data:
                path = item["dimensions"]["clientRequestPath"]
                count = item["count"]
                
                daily_visits += count
                
                # 筛选 /go/
                if path.startswith("/go/"):
                    grand_cta_data[path] += count
            
            grand_total_visits += daily_visits
            print(f" [完成! 发现 {daily_visits} 访问]")

        except Exception as e:
            print(f" [出错: {e}]")
            
        # 礼貌性暂停 0.5秒，防止请求太快
        time.sleep(0.5)

    # ================= 输出最终汇总报表 =================
    print("\n" + "="*40)
    print("📊 联盟营销点击监控报告 (7天汇总版)")
    print("="*40)
    
    # 排序
    sorted_cta = sorted(grand_cta_data.items(), key=lambda x: x[1], reverse=True)
    total_clicks = sum(grand_cta_data.values())
    
    print(f"🌍 7天总采样流量: {grand_total_visits}")
    print(f"🔥 CTA 按钮总点击: {total_clicks}")
    
    ctr = 0.0
    if grand_total_visits > 0:
        ctr = (total_clicks / grand_total_visits) * 100
    print(f"💰 综合转化率 (CTR): {ctr:.2f}%")
    
    print("\n👇 跳转链接点击详情:")
    if sorted_cta:
        for path, count in sorted_cta:
            print(f"   - {path:<25} : {count} 次")
    else:
        print("   (过去 7 天未检测到 /go/ 开头的点击)")
        
    print("="*40 + "\n")

if __name__ == "__main__":
    run_audit()