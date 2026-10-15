---
name: tum-slides
description: 用 TUM 官方 beamer 模板(tum-templates 的 tumbeamer)制作演示 slides 的通用流程、参数与踩坑记录
---

# 用 tumbeamer 制作 TUM 风格 slides

适用:任何用 TUM 官方 LaTeX 模板仓库(gitlab.lrz.de 的 tum-templates,含 `beamer/tumbeamer.cls` + `commons/*.sty` + `commons/resources/`)制作演示的场景。以下以 `<repo>` 指模板仓库根目录、`<deck>.tex` 指演示源文件。

## 编译

模板无需安装,用 TEXINPUTS 指向三个目录;目录页(TOC)需编译两遍:

```bash
T='<repo>/beamer;<repo>/commons;<repo>/commons/resources;'
TEXINPUTS="$T" pdflatex -interaction=nonstopmode -halt-on-error <deck>.tex   # ×2
```

- **PDF 被阅读器打开时编译报 "I can't write on file"**,先关闭阅读器。
- Windows/MiKTeX 下渲染自检(无 poppler/pdftoppm 时)用 MiKTeX 自带 ghostscript:
  `mgs.exe -dBATCH -dNOPAUSE -sDEVICE=png16m -r90 -dFirstPage=N -dLastPage=N -o p.png <deck>.pdf`
  (位于 `$LOCALAPPDATA/Programs/MiKTeX/miktex/bin/x64/`。)

## 文档类与关键设置

```latex
\documentclass[english, sectionpage=false]{tumbeamer}  % 16:9 默认,基准 11pt(模板钦定;4:3 为 10pt)
\provideName{\theGroupName}{<三行头第一行>}{<德文>}
\provideName{\theSchoolName}{<三行头第二行>}{<德文>}     % 第三行自动为 Technical University of Munich
\TUMbeamersetup{
  title page = TUM tower,          % 封面样式:TUM default/centered/tower/blue */shaded */flags
  content page = TUM more space,   % 或 TUM default
  headline = TUM threeliner,       % ⚠ 官方示例里的 "TUM logo threeliner" 在 v3.0 不存在,静默失效!
                                   %   合法名:TUM empty / oneliner / twoliner / threeliner
  footline = TUM default,          % = \insertfootline + 右侧单页码;另有 TUM infoline
  headline on = {every page},      % 可选集合:title page / part page / section page / content page
  footline on = {content page},
}
\footline{\insertauthor~|~<课程名>~|~<学期>}
```

- 两级标题:章 = `\frametitle`(同章各页相同),节 = `\framesubtitle`;`\section` 只供 `\tableofcontents`,`sectionpage=false` 关掉自动章页。
- modernbeamer 布局按 beamer 版本(≥2023/05/15)自动启用,不可调。
- Backup 部分置于 `\appendix` 后。

## 背景与特殊页

画布(background canvas):`TUM default`(白)/ `TUM blue`(纯蓝)/ `TUM shaded`(深蓝渐变)/ `TUM flags`(旗帜照片);叠加(background):`TUM logo`(右上)/ `TUM tower`(右下线稿)。蓝系画布会自动切换 inverse 反色主题(白字、白 logo)。

局部特殊页(目录 / Thank you / Backup 分隔页常用)的环境写法:

```latex
\newenvironment{specialframe}{\begingroup
  \setbeamertemplate{background canvas}[TUM flags]   % 或 TUM blue / TUM shaded
  \setbeamertemplate{background}[TUM logo]
  \setbeamercolor{section in toc}{fg=TUMWhite}
  \setbeamercolor{frametitle}{fg=TUMWhite}}{\endgroup}
```

- flags 照片占右半幅,文字放左半区;想让文字落在"页面中部"用 `\vspace*{0.30\textheight}` + 左对齐。

## 官方组件

- **色板**(tumcolors,自动加载):TUMBlue、TUMBlueDark/Darker/Light/Lighter、TUMOrange、**TUMGreen(注意是橄榄绿 RGB 162,173,0,不是常规绿)**、TUMGray 系、TUMIvory,另有 TUMExt 扩展色。建议:自绘结构图形(TikZ 示意图、流程链)用 TUM 色板;外部导入的数据图保留其原配色,两套并存不冲突。
- **盒子**(`\usepackage{tumboxes}`,tcolorbox 系):`TUMBox[色]{标题}`(标题条 + 描边,陈述语义)、`TUMBoxFill[色]{标题}`(浅色填充,警示/要点语义),另有 Variant/Inverse。竖向空间紧时可退化为行内 `\textcolor{TUMBlue}{\textbf{标题:}} 内容`。
- **强调**:`\alert{}` 自动渲染为 TUM 橙。
- **pifont**(`\usepackage{pifont}`):四棱花标 `\ding{118}`(❖,TUM PowerPoint 模板的列表标记,LaTeX 版没有内置);圈号 `\ding{192}`–`\ding{201}`(①–⑩)——**不要用 `\textcircled{}`,数字会超出圈体**;pdflatex+T1 下不能直接输入 unicode ①/❖。
- 目录条目样式重定义(如换 ❖、去序号):

```latex
\setbeamertemplate{section in toc}{%
  {\usebeamercolor[fg]{section in toc}\ding{118}}\hspace{0.7em}%
  {\usebeamerfont{section in toc}\usebeamercolor[fg]{section in toc}\inserttocsection}\\[0.85em]}
```

## 版面预算与溢出治理(最大坑)

16:9 + 三行头每页常驻后,内容区竖向预算很紧(约 190pt),内容稍多即 Overfull \vbox。治理流程:

1. 编译后 `grep Overfull <deck>.log`;溢出报的是 frame **结束**行号,先 `grep -n "framesubtitle\|end{frame}" <deck>.tex` 建行号-页映射再定位;
2. 全局先降一档:`\setbeamerfont{itemize/enumerate body}{size=\footnotesize}`、`\setlength{\tabcolsep}{3.5pt}`、`\renewcommand{\arraystretch}{0.95}`;
3. 图一律 `width=..., height=0.xx\textheight, keepaspectratio` 双约束(注意生效的是更紧的那个,改宽松侧无效);
4. 收敛判据:剩余溢出 ≤8pt 视觉无感可收工;>15pt 考虑**拆页**(标准:有自然切缝、拆后每页信息仍完整;图表是同一信息两种呈现的不拆)或**改左右分栏**;
5. ⚠ 纵横比 >2 的宽横多面板图(matplotlib 双面板常见)整宽放置会被高度约束压到不可读——**裁单面板**:用 pypdf 读 mediabox 得尺寸,`\includegraphics[viewport=x0 y0 x1 y1, clip, ...]`,配左右分栏,被裁面板的信息用表格或文字补回。

## TikZ 技巧

- 在引入的图上叠高亮框(不改原图 PDF),需 `\usetikzlibrary{calc}`:

```latex
\begin{tikzpicture}
  \node[anchor=south west, inner sep=0] (img) at (0,0) {\includegraphics[...]{fig.pdf}};
  \begin{scope}[shift={(img.south west)},
                x={($(img.south east)-(img.south west)$)},
                y={($(img.north west)-(img.south west)$)}]
    \draw[red, very thick, rounded corners] (0.05,0.54) rectangle (0.35,0.99);  % 图内比例坐标
  \end{scope}
\end{tikzpicture}
```

  ⚠ `(calc坐标 |- calc坐标)` 混用会报 "Giving up on this path",必须用上面的 scope 向量法;框的比例坐标靠渲染后目测校准。
- 时间轴类示意图:轴放色条**下方**、刻度再下、附加层再下,避免刻度文字被色条压住;TikZ 的 xscale/yscale 只缩放坐标不缩放字体,过度压缩时文字会溢出图形。

## 推荐的通用设计约定

- 不整句加粗,只加粗局部关键词;页面文字行尾不加句号(问号保留);少用破折号(逗号衔接,或"主句 + 次行小字"表层级);
- 次行小字宏:`\newcommand{\subnote}[1]{{\footnotesize\color{TUMGrayDark} #1}}`;
- 问答/前缀式条目:前缀粗体 + `\\` 换行放解释,比同行更清晰;
- 大数字对比页:columns 两栏 + `\fontsize{22}{24}` 级别的数字,比表格更醒目;
- 工作流:内容与布局先写成逐页大纲 md(含逐字页面文字、分栏比例、图表尺寸约束),审定后灌 tex;修改意见记入清单 md 攒批执行;每批改动后编译 + grep Overfull + 渲染 PNG 自检,收敛后才交付。
