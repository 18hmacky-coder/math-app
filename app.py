import streamlit as st
from google import genai
from PIL import Image
import re
import subprocess
import os

# ==========================================
# 🔑 ここにご自身のAPIキーを貼り付けてください
# ==========================================
API_KEY = "GEMINI_API_KEY"

# ==========================================
# 1. 完璧な初期設定（プリアンブル）※b5j修正済み
# ==========================================
LATEX_PREAMBLE = r"""\documentclass[paper=b5j, fontsize=8pt, fleqn, twoside]{jlreq}

% --- 基本パッケージ ---
\usepackage{luatexja, multicol, amsmath, amssymb, fancyhdr, enumitem, calc, varwidth}

% --- TikZ & Graphics ---
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, shapes.arrows, calc}
\usepackage[tikz]{multicolrule}
\SetMCRule{line-style=dense-solid-circles, width=0.8pt}

% --- TColorBox ---
\usepackage[most]{tcolorbox}

% --- フォント・寸法設定 ---
\makeatletter
\def\ascb@textgt#1{\textgt{#1}}
\def\ascb@gtfamily{\gtfamily}
\def\ascb@zw#1#2{#1\zw}
\newdimen\ascb@parindent@dimen
\ascb@parindent@dimen=\zw
\newcommand{\ascb@parindent}[1]{\setlength{\parindent}{#1}\relax}
\setlength{\parindent}{1\zw}

% --- Custom Box: simple (参考問題用) ---
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

% --- Custom Box: ptbs (重要事項・KEY) ---
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

% --- Custom Box: ascolorbox4A (問題文用・装飾付き) ---
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

% --- Custom Command: ascboxZ (小見出し用) ---
\tcbset{ascbox@ascolorbox/.style={after skip=1.5mm, before skip=3mm},
ascboxsizeset@ascolorbox/.style={top=0mm,bottom=0mm,right=-1mm,left=2mm,},
titleunderline@ascolorbox/.style={underlay pre={\draw[very thick,draw=gray] ([yshift=.7mm,xshift=3mm]frame.south west) -- ([yshift=.7mm]frame.south east);}}}
\DeclareTCBox{\ascboxZ}{O{dart} s O{.6} s }{
  empty,ascbox@ascolorbox,ascboxsizeset@ascolorbox,
  IfBooleanTF={#4}{}{titleunderline@ascolorbox},
  IfBooleanTF={#2}{underlay={\node[#1,thick,draw=black!40!white,fill=black!70!white,draw,inner sep=#3mm] at (frame.west) {};}}{underlay={\node[#1,thick,draw=black!70!white,fill=black!40!white,draw,inner sep=#3mm] at (frame.west) {};}}
}

% --- Header/Footer (Geometry & TikZ) ---
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

% --- 余白制御: ページ下端揃えを無効化（必須・削除禁止）---
\raggedbottom
\newcommand{\notefill}{\vfill\null}
"""

# ==========================================
# 2. Streamlit 画面構成
# ==========================================
st.set_page_config(page_title="数学解説プリント作成AI", layout="centered")
st.title("📝 数学解説プリント作成AI (PDF出力版)")

problem_text = st.text_area("問題文を入力してください", height=100)
uploaded_image = st.file_uploader("または、問題の画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_image is not None:
    st.image(uploaded_image, caption="アップロードされた問題画像", use_container_width=True)

if st.button("解説PDFを作成する"):
    if problem_text or uploaded_image:
        with st.spinner("AIがLuaLaTeXコードを生成中..."):
            try:
                client = genai.Client(api_key=API_KEY)
                
                # AIへの指示書（プリアンブルは書かせないように徹底）
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
                
                【問題文の補足】: {problem_text}
                """
                
                if uploaded_image:
                    img = Image.open(uploaded_image)
                    response = client.models.generate_content(
                        model='gemini-flash-latest', 
                        contents=[prompt, img]
                    )
                else:
                    response = client.models.generate_content(
                        model='gemini-flash-latest', 
                        contents=prompt
                    )
                
                # 生成結果からLaTeXのコードブロックを抽出
                latex_match = re.search(r"```latex\n(.*?)```", response.text, re.DOTALL)
                latex_code = latex_match.group(1) if latex_match else response.text
                
                # 万が一AIがプリアンブルや \begin{document} を書いてしまった場合に備え、本文だけを抽出・掃除する
                latex_code = latex_code.replace(r"\begin{document}", "").replace(r"\end{document}", "").strip()
                
                # 【ここがポイント！】Python側で完璧なプリアンブルと、AIが書いた本文をガッチャンコする
                final_latex = LATEX_PREAMBLE + "\n\\begin{document}\n" + latex_code + "\n\\end{document}\n"
                
                # 抽出したコードをファイルに保存
                with open("output.tex", "w", encoding="utf-8") as f:
                    f.write(final_latex)
                
                st.success("LaTeXコードの生成が完了しました！")
                
                # .tex ファイルのダウンロードボタン
                st.download_button(
                    label="📝 完璧な LaTeXソースコード (.tex) をダウンロード", 
                    data=final_latex, 
                    file_name="kaisetsu.tex",
                    mime="text/plain"
                )

                # ローカルコンパイル処理（TeXLiveが入っている場合のみ機能します）
                with st.spinner("PDFにコンパイル中... (数秒かかります)"):
                    try:
                        subprocess.run(
                            ["lualatex", "-interaction=nonstopmode", "output.tex"], 
                            check=True, 
                            capture_output=True
                        )
                        with open("output.pdf", "rb") as f:
                            pdf_data = f.read()
                        
                        st.download_button(
                            label="📥 完成したPDFをダウンロード", 
                            data=pdf_data, 
                            file_name="kaisetsu.pdf",
                            mime="application/pdf"
                        )
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        st.info("💡 上のボタンから .tex をダウンロードし、Overleafに貼り付けて「Recompile」を押せば一発で完成します！")

            except Exception as e:
                st.error(f"エラーが発生しました。\n詳細: {e}")
    else:
        st.warning("問題文を入力するか、画像をアップロードしてください。")