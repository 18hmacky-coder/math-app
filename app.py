import streamlit as st
from google import genai
from PIL import Image
import re
import subprocess
import os
import io
import hashlib
from streamlit_pdf_viewer import pdf_viewer
from streamlit_paste_button import paste_image_button

# ==========================================
# 🔑 Streamlit Cloudの金庫からAPIキーを読み込む
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]

# ==========================================
# 1. 完璧な初期設定（プリアンブル）
# ==========================================
LATEX_PREAMBLE = r"""\documentclass[paper=b5j, fontsize=8pt, fleqn, twoside]{jlreq}
\usepackage{luatexja, multicol, amsmath, amssymb, fancyhdr, enumitem, calc, varwidth}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, shapes.arrows, calc}
\usepackage[tikz]{multicolrule}
\SetMCRule{line-style=dense-solid-circles, width=0.8pt}
\usepackage[most]{tcolorbox}
\makeatletter
\def\ascb@textgt#1{\textgt{#1}}
\def\ascb@gtfamily{\gtfamily}
\def\ascb@zw#1#2{#1\zw}
\newdimen\ascb@parindent@dimen
\ascb@parindent@dimen=\zw
\newcommand{\ascb@parindent}[1]{\setlength{\parindent}{#1}\relax}
\setlength{\parindent}{1\zw}
\DeclareTColorBox{simple}{ o m O{.5} O{} }{
  empty, left=2mm, right=2mm, top=-1mm, 
  attach boxed title to top left={xshift=\ascb@zw{1.2}{11pt}}, 
  boxed title style={empty,left=-.5mm,right=-.5mm}, 
  colframe=black, coltitle=black, coltext=black, breakable, 
  before upper={\ascb@parindent{\ascb@parindent@dimen}},
  underlay unbroken={\draw[black,line width=#3pt](title.east) -- (title.east-|frame.east) -- (frame.south east) -- (frame.south west) -- (title.west-|frame.west) -- (title.west); },
  underlay first={\draw[black,line width=#3pt](title.east) -- (title.east-|frame.east) -- (frame.south east) ; \draw[black,line width=#3pt] (frame.south west) -- (title.west-|frame.west) -- (title.west); },
  underlay middle={\draw[black,line width=#3pt](frame.north east) -- (frame.south east) ; \draw[black,line width=#3pt](frame.south west) -- (frame.north west) ;},
  underlay last={\draw[black,line width=#3pt](frame.north east) -- (frame.south east) -- (frame.south west) -- (frame.north west) ;},
  fonttitle=\ascb@gtfamily, IfValueTF={#1}{title=【#2】〈#1〉}{title=【#2】}, #4
}
\newlength{\len@ptbs@kk@D}\newlength{\lenn@ptbs@kk@D}\newlength{\myfontsize@ptbs@kk@D}
\newcommand{\titlelength@ptbs@kk@D}[1]{
  \setlength{\myfontsize@ptbs@kk@D}{\f@size pt}
  \def\titletext@ptbs@D{\gtfamily\normalsize\selectfont#1}
  \settowidth{\lenn@ptbs@kk@D}{\titletext@ptbs@D}
  \setlength{\len@ptbs@kk@D}{\linewidth}
  \addtolength{\len@ptbs@kk@D}{-\lenn@ptbs@kk@D}
  \addtolength{\len@ptbs@kk@D}{-.3em}\addtolength{\len@ptbs@kk@D}{-1pt}\addtolength{\len@ptbs@kk@D}{4mm}
}
\DeclareTColorBox{ptbs}{ m O{\phantom{A}} O{} }{
  enhanced, breakable, boxsep=0mm, lefttitle=1.5mm,
  arc=.5mm, bottom=2mm, top=2mm, leftupper=4mm, rightupper=4mm,
  colbacktitle=black!100!white, colframe=black!100!white,
  coltitle=white, colback=black!10!white, boxrule=1pt, lefttitle=.3em,
  before upper={\ascb@parindent{\ascb@parindent@dimen}},
  fonttitle=\gtfamily\normalsize, fontupper=\gtfamily\normalsize,
  title={\titlelength@ptbs@kk@D{#1}#1\kern.3\zw\kern1pt},  
  after title={\tcbox[on line, boxsep=.25\myfontsize@ptbs@kk@D, boxrule=0pt, top=.1\myfontsize@ptbs@kk@D, bottom=.1\myfontsize@ptbs@kk@D, left= .5mm, right=.5mm, width=\len@ptbs@kk@D, colback=black!30!white, arc=.5mm]{\raisebox{.2ex}{\parbox{\len@ptbs@kk@D-.5\myfontsize@ptbs@kk@D-1mm}{\renewcommand{\baselinestretch}{.5}\selectfont#2}}}}, #3
}
\DeclareTColorBox{ascolorbox4A}{ o m O{3} O{}}{
  enhanced, colback=white, colframe=white,
  attach boxed title to top left={xshift=1cm,yshift=-\tcboxedtitleheight/2}, 
  varwidth boxed title=0.85\linewidth, coltitle=black, 
  fonttitle=\ascb@gtfamily, before skip=.5mm, after skip=.8mm,
  before upper={\ascb@parindent{\ascb@parindent@dimen}},
  enlarge top by=2mm, enlarge bottom by=2mm, breakable, sharp corners,
  boxed title style={colback=white,left=-.6em,right=-.6em}, 
  borderline={.75pt}{#3pt}{black,dotted},
  underlay unbroken={
    \draw[black,line width=.5pt] (title.east|-frame.north east)--([xshift=-#3*4pt]frame.north east) arc [start angle=180, end angle=270, radius=#3*4pt] -- ([yshift=#3*4pt]frame.south east) arc [start angle=90, end angle=180, radius=#3*4pt] -- ([xshift=#3*4pt]frame.south west) arc [start angle=0, end angle=90, radius=#3*4pt] -- ([yshift=-#3*4pt]frame.north west) arc [start angle=270, end angle=360, radius=#3*4pt] -- (frame.north west-|title.west) ;
    \filldraw[fill=gray,draw=gray] (frame.north east) -- ++(0,-#3*3pt) arc [start angle=270, end angle=180, radius=#3*3pt] -- cycle ;
    \filldraw[fill=gray,draw=gray] (frame.north west) -- ++(#3*3pt,0) arc [start angle=0, end angle=-90, radius=#3*3pt] -- cycle ;
    \filldraw[fill=gray,draw=gray] (frame.south west) -- ++(0,#3*3pt) arc [start angle=90, end angle=0, radius=#3*3pt] -- cycle ;
    \filldraw[fill=gray,draw=gray] (frame.south east) -- ++(-#3*3pt,0) arc [start angle=180, end angle=90, radius=#3*3pt] -- cycle ;
  },
  underlay first={
    \draw[black,line width=.5pt] (title.east|-frame.north east)--([xshift=-#3*4pt]frame.north east) arc [start angle=180, end angle=270, radius=#3*4pt] -- (frame.south east) ;
    \draw[black,line width=.5pt] (frame.south west) -- ([yshift=-#3*4pt]frame.north west) arc [start angle=270, end angle=360, radius=#3*4pt] -- (frame.north west-|title.west) ;
    \filldraw[fill=gray,draw=gray] (frame.north east) -- ++(0,-#3*3pt) arc [start angle=270, end angle=180, radius=#3*3pt] -- cycle ;
    \filldraw[fill=gray,draw=gray] (frame.north west) -- ++(#3*3pt,0) arc [start angle=0, end angle=-90, radius=#3*3pt] -- cycle ;
  },
  underlay middle={
    \draw[black,line width=.5pt] (frame.north east)--(frame.south east) ;
    \draw[black,line width=.5pt] (frame.south west)--(frame.north west) ;
  },
  underlay last={
    \draw[black,line width=.5pt] (frame.north east) -- ([yshift=#3*4pt]frame.south east) arc [start angle=90, end angle=180, radius=#3*4pt] -- ([xshift=#3*4pt]frame.south west) arc [start angle=0, end angle=90, radius=#3*4pt] -- (frame.north west) ;
    \filldraw[fill=gray,draw=gray] (frame.south west) -- ++(0,#3*3pt) arc [start angle=90, end angle=0, radius=#3*3pt] -- cycle ;
    \filldraw[fill=gray,draw=gray] (frame.south east) -- ++(-#3*3pt,0) arc [start angle=180, end angle=90, radius=#3*3pt] -- cycle ;
  },
  IfValueTF={#1}{title=【#2】〈#1〉}{title=【#2】},#4
}
\tcbset{ascbox@ascolorbox/.style={after skip=1.5mm, before skip=3mm},
ascboxsizeset@ascolorbox/.style={top=0mm,bottom=0mm,right=-1mm,left=2mm,},
titleunderline@ascolorbox/.style={underlay pre={\draw[very thick,draw=gray] ([yshift=.7mm,xshift=3mm]frame.south west) -- ([yshift=.7mm]frame.south east);}}}
\DeclareTCBox{\ascboxZ}{O{dart} s O{.6} s }{
  empty,ascbox@ascolorbox,ascboxsizeset@ascolorbox,
  IfBooleanTF={#4}{}{titleunderline@ascolorbox},
  IfBooleanTF={#2}{underlay={\node[#1,thick,draw=black!40!white,fill=black!70!white,draw,inner sep=#3mm] at (frame.west) {};}}{underlay={\node[#1,thick,draw=black!70!white,fill=black!40!white,draw,inner sep=#3mm] at (frame.west) {};}}
}
\newdimen\top@geom@TETSUMANE \top@geom@TETSUMANE=20mm
\newdimen\bottom@geom@TETSUMANE \bottom@geom@TETSUMANE=20mm
\newdimen\left@geom@TETSUMANE \left@geom@TETSUMANE=16mm
\newdimen\right@geom@TETSUMANE \right@geom@TETSUMANE=16mm
\newcommand{\Rhead@TETSUMANE}[1]{\begin{tikzpicture}[remember picture, overlay]
  \draw[line width=.5pt] ([yshift=-\top@geom@TETSUMANE+3mm, xshift=-\left@geom@TETSUMANE] current page.north east) --  ([yshift=-\top@geom@TETSUMANE+3mm, xshift=\right@geom@TETSUMANE] current page.north west);
  \node[anchor=east,yshift=-\top@geom@TETSUMANE+6mm, xshift=-\left@geom@TETSUMANE] at (current page.north east) {\footnotesize #1};
  \draw[line width=.5pt] ([yshift=\bottom@geom@TETSUMANE-3mm, xshift=-\left@geom@TETSUMANE] current page.south east) --  ([yshift=\bottom@geom@TETSUMANE-3mm, xshift=\right@geom@TETSUMANE] current page.south west);
  \node[anchor=center] at ([yshift=\bottom@geom@TETSUMANE-6mm, xshift=0.5*(-\left@geom@TETSUMANE+\right@geom@TETSUMANE)]current page.south) {\footnotesize\gtfamily\symbol{"2015}\hspace*{1ex}\thepage\hspace*{1ex}\symbol{"2015}};
\end{tikzpicture}}
\newcommand{\Lhead@TETSUMANE}[1]{\begin{tikzpicture}[remember picture, overlay]
  \draw[line width=.5pt] ([yshift=-\top@geom@TETSUMANE+3mm, xshift=\left@geom@TETSUMANE] current page.north west) --  ([yshift=-\top@geom@TETSUMANE+3mm, xshift=-\right@geom@TETSUMANE] current page.north east);
  \node[anchor=west,yshift=-\top@geom@TETSUMANE+6mm, xshift=\left@geom@TETSUMANE] at (current page.north west){\footnotesize #1};
  \draw[line width=.5pt] ([yshift=\bottom@geom@TETSUMANE-3mm, xshift=-\right@geom@TETSUMANE] current page.south east) --  ([yshift=\bottom@geom@TETSUMANE-3mm, xshift=\left@geom@TETSUMANE] current page.south west);
  \node[anchor=center] at ([yshift=\bottom@geom@TETSUMANE-6mm,xshift=0.5*(\left@geom@TETSUMANE-\right@geom@TETSUMANE)]current page.south) {\footnotesize\gtfamily\symbol{"2015}\hspace*{1ex}\thepage\hspace*{1ex}\symbol{"2015}};
\end{tikzpicture}}
\usepackage[top=\top@geom@TETSUMANE,bottom=\bottom@geom@TETSUMANE,left=\left@geom@TETSUMANE,right=\right@geom@TETSUMANE]{geometry}
\pagestyle{fancy} \renewcommand{\headrule}{} \fancyhead{} \fancyfoot{}
\fancyhead[ER]{\Rhead@TETSUMANE{\gtfamily 数学・物理 解説}}
\fancyhead[OL]{\Lhead@TETSUMANE{\gtfamily 数学・物理 解説}}
\makeatother
\raggedbottom
\newcommand{\notefill}{\vfill\null}
"""

# ==========================================
# 2. Streamlit 画面構成（モダンデザイン版）
# ==========================================
st.set_page_config(page_title="解説・添削システム", layout="centered", initial_sidebar_state="collapsed")

if "pdf_generated" not in st.session_state:
    st.session_state.pdf_generated = False

# ★追加：ペーストされた複数の画像を記憶するリスト
if "pasted_images" not in st.session_state:
    st.session_state.pasted_images = []
# 同じ画像が重複して入らないようにするためのハッシュ記憶
if "last_pasted_hash" not in st.session_state:
    st.session_state.last_pasted_hash = None

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    h1 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; letter-spacing: 1px; }
    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);
        color: white; font-weight: bold; font-size: 16px; border-radius: 12px; border: none;
        padding: 12px 24px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2); }
    .stTextArea textarea { border-radius: 10px; border: 1px solid #dcdde1; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); }
    .stRadio>div { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #f1f2f6; }
    .stFileUploader>div>div { background-color: white; border-radius: 10px; border: 2px dashed #a4b0be; }
    </style>
""", unsafe_allow_html=True)

st.title("📝 解説・添削システム")
st.markdown("<p style='color: #7f8fa6; margin-top: -10px; margin-bottom: 30px;'>最高品質のLaTeXプリントを自動生成します</p>", unsafe_allow_html=True)

app_mode = st.radio(
    "⚙️ 動作モード",
    ["📝 解説プリント作成モード", "💯 厳格な答案添削モード"],
    horizontal=True
)

max_score = 60
if app_mode == "💯 厳格な答案添削モード":
    max_score = st.number_input("💯 この問題の配点（満点）を入力してください", min_value=1, value=60, step=1)

st.markdown("<br>", unsafe_allow_html=True)

problem_text = st.text_area("✍️ テキスト入力（指示や問題文など）", height=100, placeholder="例：アップロードした画像の第2問を解説してください。")

st.markdown("### 📎 画像・PDFの読み込み")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
    paste_result = paste_image_button(
        label="📋 クリップボードからペースト", background_color="#f1f2f6", hover_background_color="#dfe4ea", text_color="#2f3542"
    )
    
    # ★追加：ペーストされた画像をリストに追加する処理
    if paste_result.image_data is not None:
        buf = io.BytesIO()
        paste_result.image_data.save(buf, format="PNG")
        img_hash = hashlib.md5(buf.getvalue()).hexdigest()
        
        if img_hash != st.session_state.last_pasted_hash:
            st.session_state.pasted_images.append(paste_result.image_data)
            st.session_state.last_pasted_hash = img_hash
    
    # ★追加：ペーストした画像が1枚以上あるときだけクリアボタンを表示
    if len(st.session_state.pasted_images) > 0:
        if st.button("🗑️ ペースト画像をクリア", key="clear_paste"):
            st.session_state.pasted_images = []
            st.session_state.last_pasted_hash = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    uploaded_files = st.file_uploader(
        "パソコンからアップロード", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, label_visibility="collapsed"
    )

target_media_list = []

if len(st.session_state.pasted_images) > 0 or uploaded_files:
    st.markdown("---")
    st.markdown("#### プレビュー")
    
# ★修正：記憶しているすべてのペースト画像を表示する
for i, img in enumerate(st.session_state.pasted_images):
    target_media_list.append(("image", img, f"pasted_image_{i}.png"))
    st.image(img, caption=f"✅ ペーストされた画像 {i+1}", use_container_width=True)

if uploaded_files:
    for f in uploaded_files:
        if f.name.lower().endswith('.pdf'):
            target_media_list.append(("pdf", f.read(), f.name))
            st.success(f"📄 PDFファイル読み込み完了: {f.name}")
        else:
            img = Image.open(f)
            target_media_list.append(("image", img, f.name))
            st.image(img, caption=f"✅ アップロード画像: {f.name}", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀 PDFを作成する"):
    if problem_text or len(target_media_list) > 0:
        with st.spinner("AIがLuaLaTeXコードを生成中..."):
            try:
                client = genai.Client(api_key=API_KEY)
                
                if app_mode == "📝 解説プリント作成モード":
                    prompt = f"""
                    1. 役割 (Role)
                    あなたは日本の最難関大学を目指す受験生のために、最高品質の解説プリントを作成する「予備校講師」兼「LaTeX組版のエキスパート」です。

                    2. 思考・解説の基準 (Content Quality)
                    ターゲット: 東大・京大・医学部志望者。
                    解説深度: ごまかしのない厳密な論理展開。定義や第一原理への言及。
                    物理・数式表記: 単位は立体、数値との間には薄いスペースを入れる。数式は文中は $ ... $、別行は \[ ... \] を使用（$$...$$ は禁止）。

                    3. デザイン・構成ルール (Design & Structure)
                    以下の指定コマンドを用いてください。
                    - 問題文: \begin{{ascolorbox4A}}[出典]{{タイトル}} ... \end{{ascolorbox4A}} （必ず冒頭に）
                    - 解説本文: \begin{{multicols*}}{{2}} ... \end{{multicols*}}
                    - 小見出し: \ascboxZ{{見出し名}}
                    - 重要事項: \begin{{ptbs}}{{KEY}}[タイトル] ... \end{{ptbs}}
                    - 類題・参考: \begin{{simple}}[出典]{{タイトル}} ... \end{{simple}}
                    - 解答の末尾: \hspace{{\zw}}\textgt{{……(答)}}

                    4. 余白制御の厳守事項 (Spacing Rules)
                    (1) \notefill は、段を切り替えた直後に左段の末尾を揃える目的でのみ使用。
                    (2) multicols* 環境の内部に \vspace, \vfill 等を不用意に挿入しない。
                    (3) 内容が少ない問題では \columnbreak を使用しない。

                    【絶対ルール】
                    \documentclass などの初期設定（プリアンブル）はシステム側で自動付与するため、**絶対に書かないでください。**
                    出力は必ず \begin{{document}} から始まり、\end{{document}} で終わるようにしてください。
                    出力全体を ```latex と ``` で囲んでください。
                    
                    【入力されたテキストの補足】: {problem_text}
                    """
                else:
                    prompt = f"""
                    1. 役割 (Role)
                    あなたは日本の最難関大学を目指す受験生を指導する、非常に厳格な予備校講師兼LaTeX組版のエキスパートです。

                    2. 添削・採点の基準 (Grading Quality)
                    提供された答案（画像またはテキスト）を以下の厳格な基準で採点・添削してください。
                    - 満点: {max_score}点満点で採点する。
                    - 採点姿勢: 採点には厳しい姿勢を貫き、論理の飛躍、計算ミス、記述の不備はすべて厳しく減点する。
                    - 必須項目: 採点結果には必ず以下の3点を見やすく含めること。
                      1. 点数（{max_score}点満点中）
                      2. 加点ポイント
                      3. 減点ポイント（減点した理由を明記）
                    - 物理・数式表記: 数式は文中は $ ... $、別行は \[ ... \] を使用（$$...$$ は禁止）。

                    3. デザイン・構成ルール (Design & Structure)
                    以下の指定コマンドを用いて、見やすい添削レポートを作成してください。
                    - タイトル・総評: \begin{{ascolorbox4A}}[添削結果]{{{max_score}点満点}} ... \end{{ascolorbox4A}} 
                    - 添削本文: \begin{{multicols*}}{{2}} ... \end{{multicols*}}
                    - 項目見出し: \ascboxZ{{見出し名}}
                    - 加点・減点の詳細: \begin{{simple}}[採点基準]{{詳細}} ... \end{{simple}}

                    4. 余白制御の厳守事項 (Spacing Rules)
                    (1) \notefill は、段を切り替えた直後に左段の末尾を揃える目的でのみ使用。
                    (2) multicols* 環境の内部に \vspace, \vfill 等を不用意に挿入しない。
                    (3) 内容が少ない場合は \columnbreak を使用しない。

                    【絶対ルール】
                    \documentclass などの初期設定（プリアンブル）はシステム側で自動付与するため、**絶対に書かないでください。**
                    出力は必ず \begin{{document}} から始まり、\end{{document}} で終わるようにしてください。
                    出力全体を ```latex と ``` で囲んでください。
                    
                    【入力されたテキストの補足】: {problem_text}
                    """
                
                content_list = [prompt]
                for idx, media_item in enumerate(target_media_list):
                    media_type, media_content, media_name = media_item
                    if media_type == "pdf":
                        temp_filename = f"temp_upload_{idx}.pdf"
                        with open(temp_filename, "wb") as f:
                            f.write(media_content)
                        gemini_file = client.files.upload(file=temp_filename)
                        content_list.append(gemini_file)
                    else:
                        content_list.append(media_content)

                response = client.models.generate_content(model='gemini-3.5-flash', contents=content_list)
                
                latex_match = re.search(r"```latex\n(.*?)```", response.text, re.DOTALL)
                latex_code = latex_match.group(1) if latex_match else response.text
                latex_code = latex_code.replace(r"\begin{document}", "").replace(r"\end{document}", "").strip()
                final_latex = LATEX_PREAMBLE + "\n\\begin{document}\n" + latex_code + "\n\\end{document}\n"
                
                with open("output.tex", "w", encoding="utf-8") as f:
                    f.write(final_latex)

                with st.spinner("自動でPDFにコンパイル中... (数秒〜十数秒かかります)"):
                    try:
                        subprocess.run(["lualatex", "-interaction=nonstopmode", "output.tex"], capture_output=True)
                        if os.path.exists("output.pdf"):
                            st.session_state.pdf_generated = True
                            st.success("✨ PDFの作成が完了しました！")
                        else:
                            st.session_state.pdf_generated = False
                            st.error("⚠️ コンパイル中に致命的なエラーが発生し、PDFが作れませんでした。")
                            st.download_button(label="📝 エラーになったコード (.tex) を確認する", data=final_latex, file_name="error.tex", mime="text/plain")

                    except FileNotFoundError:
                        st.session_state.pdf_generated = False
                        st.error("⚠️ サーバー側にLaTeXシステムがまだインストールされていません。")
                    except Exception as e:
                        st.session_state.pdf_generated = False
                        st.error(f"⚠️ 予期せぬエラーが発生しました。\n詳細: {e}")

            except Exception as e:
                st.error(f"エラーが発生しました。\n詳細: {e}")
    else:
        st.warning("指示を入力するか、画像やPDFをアップロードしてください。")

# ==========================================
# プレビュー表示
# ==========================================
if st.session_state.get("pdf_generated", False) and os.path.exists("output.pdf"):
    st.markdown("---")
    st.markdown("### 📄 完成したPDF")
    
    with open("output.pdf", "rb") as f:
        pdf_data = f.read()
    
    pdf_viewer("output.pdf")
    
    st.download_button(
        label="📥 このPDFを保存する", 
        data=pdf_data, 
        file_name="output.pdf",
        mime="application/pdf"
    )
