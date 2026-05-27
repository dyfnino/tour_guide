"""
课程文件上传 e2e 诊断：
1. 创建测试图/视频/音频字节流，POST /api/uploads
2. 验证返回的 url 可 GET 200
3. 创建一个课程绑定上传后的 url
4. 验证 GET /api/courses/{id} 返回的 image / media_url 与上传一致

依赖运行中的后端，默认 http://localhost:8000，可用 BASE 环境变量覆盖
"""
import io
import os
import sys
import requests

BASE = os.getenv("BASE", "http://localhost:8000")


def show(name, ok, detail=""):
    tag = "[OK]" if ok else "[FAIL]"
    print(f"{tag} {name}{(' -- ' + detail) if detail else ''}")


def main():
    # 1) 上传图片
    r = requests.post(BASE + "/api/uploads",
                      files={"file": ("cover.png", b"\x89PNG\r\n\x1a\nfake", "image/png")},
                      data={"kind": "image"}, timeout=10)
    show("上传封面图", r.ok, f"{r.status_code}")
    if not r.ok:
        print(r.text); sys.exit(1)
    img = r.json()
    print("   image url:", img["url"])

    # 2) 上传视频
    r = requests.post(BASE + "/api/uploads",
                      files={"file": ("lec.mp4", b"FAKEMP4", "video/mp4")},
                      data={"kind": "video"}, timeout=10)
    show("上传视频", r.ok, f"{r.status_code}")
    vid = r.json()
    print("   video url:", vid["url"])

    # 3) 静态文件可访问
    r = requests.get(img["url"], timeout=5)
    show("封面 URL 可访问", r.ok and len(r.content) > 0, f"{r.status_code} bytes={len(r.content)}")

    r = requests.get(vid["url"], timeout=5)
    show("视频 URL 可访问", r.ok and len(r.content) > 0, f"{r.status_code} bytes={len(r.content)}")

    # 4) 创建课程，绑定上传 URL
    payload = {
        "name": "e2e上传测试课",
        "description": "由诊断脚本创建",
        "price": 1, "category": "basic",
        "media_type": "video",
        "media_url": vid["url"],
        "image": img["url"],
        "is_active": True,
    }
    r = requests.post(BASE + "/api/courses", json=payload, timeout=10)
    show("创建课程绑定上传媒体", r.status_code == 201, f"{r.status_code}")
    if r.status_code != 201:
        print(r.text); sys.exit(1)
    cid = r.json()["id"]
    r = requests.get(f"{BASE}/api/courses/{cid}", timeout=5)
    course = r.json()
    show("课程 image / media_url 字段一致", course["image"] == img["url"] and course["media_url"] == vid["url"])
    print(f"   course #{cid}: image={course['image']}, media_url={course['media_url']}")


if __name__ == "__main__":
    main()