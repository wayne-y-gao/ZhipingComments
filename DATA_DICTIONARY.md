# 脂批（批注/评语）数据集：变量说明（Data Dictionary）

本仓库包含从《石头记/红楼梦》纯文本（TXT）自动抽取的批注/评语（“脂批”）数据集。每一行对应一个“批语单元”（通常是一个【……】括号块中的一条带标签批语；若同一括号块内含多条标签批语，会拆分为多行）。

## 文件
- `ShiTouJi.txt`：石头记/红楼梦原始文本，其中【……】括号块内包含批语。
- `ZhipiComments.csv`：主数据集（本仓库的“可分析数据”）。
- `BuildCommentsData.py`：复现脚本（从 TXT 生成 CSV）。
- `LICENSE`：GPL-3.0 许可（适用于脚本/代码；对文本与数据的版权归属请自行核验）。

> 注意：作品《红楼梦》本体已属公有领域，但具体电子整理版/标点/汇编格式可能存在权利主张。将原文全文（TXT）公开前，请自行确认来源与再分发权限。

---

## 列说明（按 CSV 列顺序）

### A. 由 TXT 文本直接抽取/可“指认于原文”的字段（factual）

- `comment_id`：批语单元的顺序编号（按文档自前至后扫描产生，1 起始）。
- `chapter_number`：回目序号（从“第X回 …”标题解析，阿拉伯数字）。
- `chapter_title`：当前回目标题的原文行（保留原文中的括号/空白/制表符等）。
- `section`：文档中的非回目分区标题（目前主要识别“戚蓼生序”“甲戌本凡例”等）。
- `doc_part`：`toc` / `body`。依据章节标题是否带页码制表符及其位置粗分“目录/正文”。
- `is_toc_entry`：是否为目录型回目行（1/0）。
- `paragraph_index`：批语所在的 TXT 行号（对应原 DOCX 段落序号，从 0 计）。
- `paragraph_in_chapter`：该段落相对本回目标题段落的偏移（标题段为 0）。
- `bracket_index_in_paragraph`：同一段落内第几个“【…】”括号块（从 0 计）。
- `unit_index_in_bracket`：同一括号块内第几个批语单元（从 0 计）。
- `bracket_char_start`：括号块起始“【”在起始段落内的字符索引（从 0 计）。
- `bracket_char_end`：括号块结束“】”在起始段落内的结束索引（**左闭右开**）。若跨段落，则为空。
- `bracket_end_paragraph_index`：括号块结束所在段落序号（可能等于 `paragraph_index`）。
- `bracket_end_char_end`：括号块结束“】”在结束段落内的结束索引（左闭右开）。
- `bracket_spans_paragraphs`：括号块是否跨段落（1/0）。
- `doc_global_start`：括号块起始“【”在整份 TXT（以 `\n` 连接）中的全局字符索引。
- `doc_global_end`：括号块结束“】”之后的位置在整份 TXT 中的全局字符索引（左闭右开）。
- `label_raw`：批语标签的原始形态（如“甲戌侧批”“庚辰眉批”“蒙侧批”等）。若括号块内存在未带标签的文字段，则为空。
- `bracket_text_raw`：括号块内部原文（不含外侧“【】”，保留换行）。
- `comment_text_raw`：批语内容原文（去掉标签与冒号后的部分；尽量保留原始空白/换行）。
- `signature_exact`：在批语内容中识别到的“署名”原文片段（若有）。
- `date_text`：在批语内容末尾识别到的干支/季节等日期原文片段（若有）。
- `colophon_extra`：预留字段（用于记录极少数残缺“尾题”信息；当前版本通常为空）。
- `anchor_before`：括号块前 80 字符的段内定位片段（便于人工回看）。
- `anchor_after`：括号块后 80 字符的段内定位片段。
- `paragraph_main_text`：将本段落内所有【…】括号块移除后的“正文”文本（为空则记空）。
- `context_before_60`：括号块起点前 60 个全局字符窗口（跨段落）。
- `context_after_60`：括号块终点后 60 个全局字符窗口（跨段落）。

### B. 由文本规则归一化/派生得到的字段（deterministic derived; 仍仅依赖 TXT）

- `label_norm`：`label_raw` 去除空白后的规范形态（便于分组统计）。
- `prefix_raw`：从 `label_norm` 提取的前缀（如“甲戌”“庚辰”“己卯”“蒙”“靖”“脂”等）。
- `prefix_norm`：`prefix_raw` 的去空白版本。
- `manuscript_version`：据 `prefix_norm` 映射的抄本系统（如“甲戌本”“庚辰本”“己卯本”；无法判定则为空）。
- `comment_type`：据 `label_norm` 识别的批语类型（如“眉批”“侧批”“双行夹批”“回末总批”等；无法判定则为空）。
- `comment_text_clean`：用于分析的“净化”批语文本（去除前置署名标记、尾部署名与日期、以及末尾常见标点）。
- `char_len`：`comment_text_clean` 的字符长度。
- `has_signature`：是否识别到署名（1/0）。
- `signature_norm`：`signature_exact` 去空白并做轻度归并后的形态（例如将“脂批”归并到“脂”）。
- `signature_position`：署名位置：`suffix`（末尾）/ `prefix_text`（前缀）/ `prefix_label`（标签即署名）。
- `signature_source`：署名提取来源类型（如 `suffix_strict` / `suffix_spaced` / `prefix_marker` / `label_author`）。
- `signature_scope`：署名作用域（当前主要为 `main`）。
- `signature_marker`：前缀署名中识别到的标记词（如“再笔”等；若无则为空）。
- `signature_confidence`：署名识别置信标签（当前仅对少量情况标记）。
- `has_date`：是否识别到日期（1/0）。
- `date_ganzhi`：从 `date_text` 提取的干支对（如“甲戌”“壬午”等）。
- `date_ganzhi_source`：`date_ganzhi` 提取来源（当前为 `suffix`）。
- `date_year_est`：将干支映射到公历年份的估计值（仅对少量常见干支做了固定映射；未知则为空）。
- `date_qianlong_year_est`：对应乾隆年号的估计值（= `date_year_est - 1735`）。
- `comment_period_est`：依据 `date_year_est` 的粗分期：`early_<=1760` / `late_>=1762`。
- `commenter_standard`：标准化批者名（若标签为“蒙/靖”则直接赋值；若有署名则归并到“脂砚斋/畸笏叟”；否则为空）。
- `commenter_confidence`：批者识别置信：`high`（署名直接支持）/ `medium`（仅标签支持）/ 空。
- `extraction_note`：预留字段（记录抽取异常/需人工核查的提示；当前版本通常为空）。

### C. 基于“脂砚斋为主”的先验/概率化字段（probabilistic; 仅作分析特征，不是定论）

这些字段用于在 **绝大多数无署名批语** 情况下提供可量化的“归属倾向”特征，以支持统计分析（例如比较脂砚斋与畸笏叟的风格差异）。它们不应被直接当作作者判定。

- `prior_zhi_dom`：批语归于“脂砚斋”的先验概率。
- `prior_jihu_dom`：批语归于“畸笏叟”的先验概率。
- `prior_other_dom`：批语归于“其他批者”的先验概率（如“蒙”“靖”等）。
- `prior_basis_dom`：本行先验计算所用的规则标签（例如是否有署名、是否为晚期日期、是否为特定抄本+批型等）。
- `prior_label_dom`：在该先验规则下的“优势类别”标签（如 `脂砚斋_prior` / `畸笏叟_prior` / `蒙` / `靖` 等）。

---

## 复现方法（概要）

1. 获取并确定在仓库中存在带有脂评的红楼梦原始文本 `ShiTouJi.txt`。
2. 运行：
   ```bash
   python BuildCommentData.py      --input ShiTouJi.txt      --output ZhipiCommentsRep.csv
   ```
3. 生成的 CSV 应与仓库版本一致（同列顺序、同规则）。


## 参考
- 维基百科：脂批（背景说明与版本概览） https://zh.wikipedia.org/zh-hans/%E8%84%82%E6%89%B9
