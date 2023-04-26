import datetime
import requests
from config_file import config_data

def get_credit_summary_by_index(index):
    subscription_url = "https://gpt.lucent.blog/v1/dashboard/billing/subscription"
    headers = {
        "Authorization": "Bearer " + config_data['openai']['api_key'][index],
        "Content-Type": "application/json"
    }
    subscription_response = requests.get(subscription_url, headers=headers)
    if subscription_response.status_code == 200:
        data = subscription_response.json()
        print(data)
        total = data.get("hard_limit_usd")
    else:
        return subscription_response.text
    end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.datetime.now() + datetime.timedelta(days=-30)).strftime("%Y-%m-%d")
    billing_url = "https://gpt.lucent.blog/v1/dashboard/billing/usage?start_date="+ start_date + "&end_date=" + end_date
    billing_response = requests.get(billing_url, headers=headers)
    if billing_response.status_code == 200:
        data = billing_response.json()
        total_usage = data.get("total_usage") / 100
        daily_costs = data.get("daily_costs")
        days = min(3, len(daily_costs))
        recent = f"最近{days}天使用情况:  \n"
        for i in range(days):
            cur = daily_costs[-i - 1]
            date = datetime.datetime.fromtimestamp(cur.get("timestamp")).strftime("%Y-%m-%d")
            line_items = cur.get("line_items")
            cost = 0
            for item in line_items:
                cost += item.get("cost")
            recent += f"\t{date}\t{cost / 100} \n"
    else:
        return billing_response.text

    return f"#Key_{str(index +1)}  \n" \
           f"总额:\t{total:.2f}  \n" \
           f"已用:\t{total_usage:.2f}  \n" \
           f"剩余:\t{total - total_usage:.2f}  \n" \
           f"" + recent
