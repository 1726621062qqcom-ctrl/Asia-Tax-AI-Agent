% File: tumexam.cls Copyright (C) 2022 The LaTeX4EI Team
% Provides an exam template in the TUM Corporate Design.
%
% It may be distributed and/or modified under the conditions of the
% LaTeX Project Public License (LPPL), either version 1.3c of this
% license or (at your option) any later version. The latest version
% of this license is in the file
%
%    https://www.latex-project.org/lppl.txt
%
% This file is part of the "tum-templates bundle" (The Work in LPPL)
% and all files in that bundle must be distributed together.
%
%
% ----------------------------------------------------------------------------
%
% The development version of the bundle can be found at
%
%    https://gitlab.lrz.de/latex4ei/tum-templates
%
% for those people who are interested.
%
% ----------------------------------------------------------------------------
%
% Version history:
% v3.0 2024/05/24 Initial version.
%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{tumexam}[2024/05/24 v3.0]


% .:: Load required packages
% ----------------------------------------------------------------------------

\RequirePackage{placeins}
\RequirePackage{pgfkeys}
\RequirePackage{pgfopts}


% .:: Package options for tumexam class
% ----------------------------------------------------------------------------

\ProcessPgfOptions{/TUM/exam}


% .:: Load base class
% ----------------------------------------------------------------------------

% print debug info to logfile
\typeout{Global options before any option parsing.}
\typeout{classoptions: \@classoptionslist}
\typeout{unused classoptions: \@unusedoptionlist}

% pass options to exam
\PassOptionsToClass{addpoints}{exam}
% pass tumexam class options down to exam
\PassOptionsToClass{\@classoptionslist}{exam}
\LoadClass{exam}

% print debug info to logfile
\typeout{Global options after exam option parsing.}
\typeout{classoptions: \@classoptionslist}
\typeout{unused classoptions: \@unusedoptionlist}


% .:: Override exam layout commands
% ----------------------------------------------------------------------------

\let\chead\relax
\let\@chead\relax
\let\cfoot\relax
\let\@cfoot\relax


% .:: Extend exam class with KOMA-Script
% ----------------------------------------------------------------------------

\RequirePackage[extendedfeature=title]{scrextend}


% .:: Load TUM packages
% ----------------------------------------------------------------------------

\RequirePackage{tumbase}
\RequirePackage{tumcolors}
\RequirePackage{tumlogo}
\RequirePackage{tumlang}
\RequirePackage{tumauthblk}
\RequirePackage{tumcaptions}
\RequirePackage{tumpage}
\RequirePackage{tumfonts}
\RequirePackage{tumboxes}
\RequirePackage{tumuser}


% .:: Definitions
% ----------------------------------------------------------------------------

\newcommand{\theStudentBlock}{~}
\newcommand{\studentblock}[1]{\renewcommand{\theStudentBlock}{#1}}
\newcommand{\theDisclaimer}{~}
\newcommand{\disclaimer}[1]{\renewcommand{\theDisclaimer}{#1}}

% .:: Layout
% ----------------------------------------------------------------------------

% layers for TUM pagenumber exam
\DeclareNewLayer[clone = TUM.foot.base.oneside,
  contents = {\hfill\usekomafont{pagenumber}\thepage~/~\pageref{LastPage}}
]{TUM.foot.exampagenumber.oneside}
\DeclareNewLayer[clone = TUM.foot.base.odd,
  contents = {\hfill\usekomafont{pagenumber}\thepage~/~\pageref{LastPage}}
]{TUM.foot.exampagenumber.odd}
\DeclareNewLayer[clone = TUM.foot.base.even,
  contents = {\usekomafont{pagenumber}\thepage~/~\pageref{LastPage}}
]{TUM.foot.exampagenumber.even}

% inside pagestyle (no header, only page numbers)
\DeclareNewPageStyleByLayers[
  onselect = {\pgfkeys{/TUM/page/layout=insidepage}\@tum@activate@layout@}
]{TUM.insidepage.exam}{%
  TUM.foot.exampagenumber.oneside,%
  TUM.foot.exampagenumber.odd,%
  TUM.foot.exampagenumber.even,%
}

% page style for the title page including the TUM logo and headline
\DeclareNewPageStyleByLayers{TUM.exam.titlepage}{%
  TUM.head.tumlogo.oneside,%
  TUM.head.tumlogo.odd,%
  TUM.head.tumlogo.even,%
  TUM.head.headline.oneside,%
  TUM.head.headline.odd,%
  TUM.head.headline.even,%
  TUM.foot.exampagenumber.oneside,%
  TUM.foot.exampagenumber.odd,%
  TUM.foot.exampagenumber.even,%
}

% define titlepagestyle command
\newcommand{\titlepagestyle}{TUM.exam.titlepage}

% load the default pagestyle for exams
\pagestyle{TUM.insidepage.exam}


% .:: Fonts
% ----------------------------------------------------------------------------

% title block fonts
\setkomafont{title}{\sffamily\LARGE\bfseries}
\setkomafont{subtitle}{\sffamily\large\mdseries}
\setkomafont{author}{\sffamily\large\bfseries\textcolor{TUMBlue}}
\newkomafont{affiliation}{\sffamily\small\mdseries}
\setkomafont{date}{\sffamily\footnotesize\mdseries}
\newkomafont{studentblock}{\sffamily\mdseries}
\newkomafont{disclaimer}{\sffamily\mdseries}
\newkomafont{gradetable}{\sffamily\mdseries}

\newkomafont{exercise-title}{\sffamily\Large\bfseries}
\newkomafont{exercise-description}{\sffamily\mdseries}

% avoid buggy handling of numbers in URLs
\renewcommand\UrlFont{\normalfont}


% .:: Custom title
% ----------------------------------------------------------------------------

\renewcommand{\@maketitle}{
  \newpage
  \begingroup
  \raggedright
  \ifdefempty{\@subtitle}{}{
    {\usekomafont{subtitle}\@subtitle\par}
    \vspace{.4em}
  }
  {\usekomafont{title}\@title\par}
  \vspace{1.5em}
  {\usekomafont{author}\@author\par}
  \vspace{.4em}
  {\usekomafont{affiliation}\theAffil\par}
  \ifdefempty{\theEmail}{}{
    \vspace{.25em}
    {\usekomafont{affiliation}\theEmail\par}
  }
  \ifdefstring{\@date}{}{}{
    \vspace{.25em}
    {\usekomafont{date}\@date\par}
  }
  \vspace{5em}
  \ifdefempty{\theStudentBlock}{}{
    {\usekomafont{studentblock}\theStudentBlock}
    \vspace{2em}
  }
  \ifdefempty{\theDisclaimer}{}{
    {\usekomafont{disclaimer}\theDisclaimer}
  }
  \endgroup
  \vfill
  \centering
  \begingroup
  {\usekomafont{gradetable}
    \hqword{\questionTag{}:}% substitutes text for “Question:”
    \hpword{\totalPointTag{}:}% substitutes text for “Points:”
    \hsword{\scoreTag{}:}% substitutes text for “Score:”
    \htword{\textbf{\totalTag{}}}% substitutes text for “Total”
    \ifnum10>0\numquestions\relax
      \gradetable[h][questions]%
    \else
      \multirowgradetable{2}[questions]%
    \fi%
  }
  \endgroup
  \vspace{1.5em}
  \FloatBarrier
}


% .:: Set default PDF metadata
% ----------------------------------------------------------------------------

\AtBeginDocument{
  \def\@tum@pdftitle@{\@title\ifdefempty{\@subtitle}{}{~-~\@subtitle}}
  \hypersetup{
    pdftitle = {\@tum@pdftitle@},
    pdfauthor = {\pgfkeysvalueof{/TUM/author list}},
    pdfsubject = {\@subject},
    % pdfkeywords = {},
    pdfcreator = {\theUniversityName}
  }
}


% open bookmarks tree, use SinglePage layout
\hypersetup{
  bookmarksnumbered = true,
  bookmarksopen = true,
  bookmarksopenlevel = 1,
  pdfpagemode=UseOutlines,
  pdfpagelayout=SinglePage,
}


% .:: Custom definitions
% ----------------------------------------------------------------------------

% label questions in question table with question number instead of title
\patchcmd{\questions}
{\def\@currentlabel{\thequestiontitle}}
{\def\@currentlabel{\thequestion}}
{}
{}

% format titled question headings
\setlength{\rightpointsmargin}{1.5cm}
\pointpoints{\singlePointTag}{\multiplePointsTag}
\qformat{\raggedright
  {\usekomafont{exercise-title}\questionTag{}~\thequestion}%
  {\usekomafont{exercise-description}\quad\thequestiontitle\quad(\thepoints)}%
  \protect\rule[-2.2ex]{0ex}{2.2ex}\hfill
}
\renewcommand{\questionshook}{%
  \setlength{\leftmargin}{0pt}%
  \setlength{\labelwidth}{-\labelsep}%
}

% alphabetic part numbering
\renewcommand{\thepartno}{\alph{partno}}
\renewcommand{\partlabel}{\thepartno)}

% define independent part marked with an asterisk
\newcommand\independentpart{\renewcommand\partlabel{\thepartno)%
    \makebox[0pt]{$\ ^\ast$}}%
  \part
}

% define dependent part (complementary to independent part) without asterisk
\newcommand\dependentpart{\renewcommand\partlabel{\thepartno)}%
  \part
}

% define solution title for solution boxes if answers are printed
\renewcommand{\solutiontitle}{\noindent\textbf{\solutionTag{}:}\par\noindent}

% define empty boxes for additional space (if required)
\newcommand{\makenonemptybox}[2]{%
  \par\nobreak\vspace{\ht\strutbox}\noindent
  \fbox{%
    \parbox[c][\dimexpr#1-2\fboxsep][t]{\dimexpr\linewidth-2\fboxsep}{
      \hrule width \hsize height 0pt
      #2
    }%
  }%
  \par\vspace{\ht\strutbox}
}

% provide English and German labels
\provideName{\singlePointTag}{point}{Punkt}
\provideName{\multiplePointsTag}{points}{Punkte}
\provideName{\totalPointTag}{Points}{Punktzahl}
\provideName{\questionTag}{Problem}{Aufgabe}
\provideName{\scoreTag}{Score}{Davon erreicht}
\provideName{\totalTag}{Total}{Summe}
\provideName{\solutionTag}{Solution}{Lösung}
