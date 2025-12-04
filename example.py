import os
import requests
import urllib.parse
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from wordcloud import WordCloud
import streamlit as st

# ====== 설정 ======
POTENS_API_URL = "https://ai.potens.ai/api/chat"
# 🔥 네 Potens API Key 직접 입력 (원하면 여기만 바꿔도 됨)
POTENS_API_KEY = "YRkzMbdIwkfjYFGKRGmkNOA83tEFzOzy"


# ====== Potens AI 호출 (기업 요약) ======
def call_potens_ai(company_name: str) -> str:
    if not POTENS_API_KEY:
        return "❌ POTENS_API_KEY가 코드에 설정되어 있지 않습니다."

    prompt = f"""
당신은 기업 분석을 도와주는 전문 애널리스트입니다.

아래 기업에 대해 한국어로 이해하기 쉽게 정리해 주세요.

[기업명]
{company_name}

[요청사항]
- 마크다운 형식으로 작성
- 너무 장황하지 않게, 핵심 위주로 정리

[출력 항목]
1. 한 줄 요약
2. 회사 개요 (설립연도, 업종, 주요 사업 등)
3. 핵심 사업/서비스
4. 투자/비즈니스 관점에서의 강점
5. 리스크 요인
6. 최근 주요 이슈 (알고 있는 범위 내에서 bullet list)
""".strip()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {POTENS_API_KEY}",
    }
    data = {"prompt": prompt}

    try:
        resp = requests.post(POTENS_API_URL, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        return body.get("message", "AI 응답을 파싱할 수 없습니다.")
    except Exception as e:
        return f"❌ Potens API 호출 오류: {e}"


# ====== Google News RSS에서 최신 기사 20개 ======
def fetch_google_news(company_name: str, max_results: int = 20):
    encoded_query = urllib.parse.quote(company_name)
    url = (
        f"https://news.google.com/rss/search?q={encoded_query}"
        "&hl=ko&gl=KR&ceid=KR:ko"
    )

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        return [], f"뉴스를 가져오는 중 오류가 발생했습니다: {e}"

    try:
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        articles = []
        for item in items[:max_results]:
            raw_title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            description = (item.findtext("description") or "").strip()

            # 제목에서 출처 분리: "제목 - 매체명"
            source = ""
            title = raw_title
            if " - " in raw_title:
                title, source = raw_title.rsplit(" - ", 1)
                title = title.strip()
                source = source.strip()

            # description 안의 href에서 실제 기사 링크 추출 시도
            real_link = link
            if 'href="' in description:
                start = description.find('href="') + len('href="')
                end = description.find('"', start)
                if start > -1 and end > -1:
                    real_link = description[start:end]

            articles.append(
                {
                    "title": title or raw_title,
                    "source": source,
                    "link": real_link,
                    "pub_date": pub_date,
                }
            )
        return articles, ""
    except Exception as e:
        return [], f"뉴스 RSS 파싱 중 오류가 발생했습니다: {e}"


# ====== 워드클라우드 생성 ======
def create_wordcloud_from_articles(articles):
    text_parts = [a.get("title", "") for a in articles]
    text = " ".join(text_parts)

    if not text.strip():
        return None, "워드클라우드를 생성할 텍스트가 없습니다."

    # 한글 폰트 경로 (WSL/리눅스/윈도우 고려)
    font_path = None
    candidate_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumSquareNeo-bRg.ttf",
        "/mnt/c/Windows/Fonts/malgun.ttf",  # WSL에서 윈도우 한글 폰트
        "/mnt/c/Windows/Fonts/NGULIM.TTF",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            font_path = path
            break

    try:
        wc = WordCloud(
            width=800,
            height=400,
            background_color="white",
            font_path=font_path,
        ).generate(text)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        plt.tight_layout()
        return fig, ""
    except Exception as e:
        return None, f"워드클라우드를 생성하는 중 오류가 발생했습니다: {e}"


# ====== 스타일 (토스 느낌 + 큰 섹션 제목 + 예쁜 검색창) ======
def inject_toss_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: #f4f6fa;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
        }

        .main-title {
            padding-top: 1.5rem;
            padding-bottom: 0.5rem;
        }

        .pill {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 500;
            background: #eff4ff;
            color: #3b82f6;
            margin-top: 0.1rem;
        }

        h1 {
            font-size: 2.2rem;
            font-weight: 700;
        }

        h2 {
            font-size: 1.6rem;
            font-weight: 700;
        }

        /* 검색 영역 */
        .search-wrapper {
            margin-top: 1.6rem;
            margin-bottom: 1.2rem;
        }

        .search-label {
            font-size: 0.95rem;
            font-weight: 600;
            color: #4b5563;
            margin-bottom: 0.25rem;
        }

        input[type="text"] {
            border-radius: 999px !important;
            border: 1px solid #d1d5db !important;
            padding: 0.55rem 1rem !important;
            background: #ffffff !important;
            font-size: 0.95rem !important;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.05);
        }

        .stButton button {
            background: #3182f6;
            color: white;
            border-radius: 999px;
            padding: 0.55rem 1.4rem;
            border: none;
            font-weight: 600;
            font-size: 0.95rem;
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
        }
        .stButton button:hover {
            background: #2563eb;
        }

        /* 섹션 대제목 pill */
        .section-title {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #ffffff;
            padding: 0.55rem 1.3rem;
            border-radius: 999px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.10);
            border: 1px solid #e5e7eb;
            margin-top: 2.0rem;
            margin-bottom: 0.6rem;
        }
        .section-title-icon {
            font-size: 1.35rem;
        }
        .section-title-text {
            font-size: 1.45rem;
            font-weight: 700;
        }

        hr {
            margin: 0.7rem 0 0.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ====== 메인 앱 ======
def main():
    st.set_page_config(page_title="AI 기업분석", layout="wide")
    inject_toss_style()

    # 상단 타이틀
    st.markdown(
        """
        <div class="main-title">
            <h1>AI 기업분석</h1>
            <span class="pill">베타 · Potens AI 기반</span>
            <p style="color:#6b7280; margin-top:0.6rem; font-size:0.9rem;">
                알고 싶은 회사를 검색하면, AI가 기업 개요를 정리하고 구글 뉴스에서 최신 이슈를 모아드립니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- 검색 영역 (예쁜 검색창 + 아래 버튼) ----
    st.markdown('<div class="search-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="search-label">기업명 검색</div>', unsafe_allow_html=True)
    st.caption("분석하고 싶은 기업명을 입력하고 아래 버튼을 눌러보세요.")

    company_query = st.text_input(
        label="기업명 입력",
        placeholder="예: 삼성전자, 카카오, 네이버, 하나저축은행 등",
        label_visibility="collapsed",
    )

    # 버튼: 가운데 정렬 느낌
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 2])
    with btn_col2:
        search_clicked = st.button("기업 분석하기", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if not search_clicked:
        return

    company = company_query.strip()
    if not company:
        st.warning("먼저 기업명을 입력해 주세요.")
        return

    # 1) 기업 요약
    with st.spinner(f"AI가 '{company}' 기업을 분석하는 중입니다..."):
        summary_md = call_potens_ai(company)

    # 2) 뉴스
    with st.spinner(f"'{company}' 관련 최신 뉴스를 가져오는 중입니다..."):
        articles, news_err = fetch_google_news(company)

    # ---- 기업 요약 섹션 ----
    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown(
            """
            <div class="section-title">
                <span class="section-title-icon">📌</span>
                <span class="section-title-text">기업 요약</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("AI가 공개된 정보를 기반으로 정리한 내용입니다.")
        st.markdown("---")
        st.markdown(summary_md)

    # ---- 최신 뉴스 섹션 ----
    with right_col:
        st.markdown(
            """
            <div class="section-title">
                <span class="section-title-icon">📰</span>
                <span class="section-title-text">최신 뉴스 (Google News)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("최신순으로 최대 20개 뉴스를 보여줍니다.")
        st.markdown("---")

        if news_err:
            st.error(news_err)
        elif not articles:
            st.info("표시할 뉴스가 없습니다.")
        else:
            for a in articles:
                title = a["title"] or "제목 없음"
                link = a["link"]
                pub_date = a["pub_date"]
                source = a["source"]

                if link:
                    st.markdown(f"- [{title}]({link})")
                else:
                    st.markdown(f"- {title}")

                meta_parts = []
                if pub_date:
                    meta_parts.append(pub_date)
                if source:
                    meta_parts.append(source)
                if meta_parts:
                    st.caption(" · ".join(meta_parts))

    # ---- 워드클라우드 섹션 ----
    st.markdown(
        """
        <div class="section-title">
            <span class="section-title-icon">☁</span>
            <span class="section-title-text">뉴스 키워드 워드클라우드</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("위 20개 뉴스의 제목을 기반으로 키워드를 시각화합니다.")
    st.markdown("---")

    if articles:
        fig, wc_err = create_wordcloud_from_articles(articles)
        if wc_err:
            st.error(wc_err)
        elif fig is None:
            st.info("워드클라우드를 생성할 수 있는 텍스트가 부족합니다.")
        else:
            st.pyplot(fig)
    else:
        st.info("먼저 뉴스가 조회되어야 워드클라우드를 생성할 수 있습니다.")


if __name__ == "__main__":
    main()
