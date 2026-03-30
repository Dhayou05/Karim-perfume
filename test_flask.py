import requests
s = requests.Session()
s.get('http://127.0.0.1:5000/')
for i in range(10):
    res = s.post(f'http://127.0.0.1:5000/question/{i}', data={'answer': '0'}, allow_redirects=False)
    if res.status_code == 302:
        print(f"Q{i} redirected to: {res.headers['Location']}")
    else:
        print(f"Q{i} returned: {res.status_code}")

res = s.get('http://127.0.0.1:5000/result', allow_redirects=True)
print("Result status:", res.status_code)
print("Errors in output?", "Traceback" in res.text or "Error" in res.text)
if "Traceback" in res.text:
    print(res.text[:1000])
