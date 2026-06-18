# 競合・他参加者プロダクト調査レポート

> 作成日: 2026年6月18日 / 調査手法: deep-research（5アングル並列Web調査 → 突合・重複排除）
> 位置づけ: pmz の **新規性の裏取り** と **審査での立ち位置** を確定するための競合インテリジェンス。
> 関連: 審査傾向 → `judges-analysis.md` / `judging-criteria-strategy.md` ／ 要件正本 → `../requirements.md`
>
> ⚠️ 調査制約: Zenn / note / Devpost / Findy / connpass / prtimes は WebFetch が軒並み **HTTP 403**（botブロック）。
> 一次本文を全文取得できたのは **Google Cloud 公式ブログ2本のみ**。それ以外は検索スニペット＋
> Zenn/Google Cloud 公式 X の受賞告知に依拠する。各項に【確認済み】【確度中】【推測】を明示。

---

## 0. TL;DR（3行）

1. **pmz の核2軸＝①要件定義書ベースのPM観点判定 ②リリース結果から学習する自己改善ループ、を"両方"持つ作品は、ハッカソン作品・商用ツールいずれの調査範囲でも見つからなかった**（＝新規性は守れている）。
2. ただし **個別機能はすでに既出**：「PRゲートでGo/No-Go」はGitLab系ハッカソン作 **TrustOps**、「要件充足判定」は **Qodo / Atlassian Rovo Dev**、「障害結果から学習」は **ReleaseGate.ai / Meta DRS**。→ ピッチでは「リリースゲート」一般ではなく **X×Y×Z の交差点** を新規性の核に据えるべき。
3. 本ハッカソン（2026）特有の加点軸は公式明言で **「まわす＝自己改善サイクルを自分で回す」「エージェントの必然性・自律判断設計」「本番品質」**。pmz の自己改善ループ＋条件付き自律＋ハードガード/監査ログはテーマに直撃。

---

## 1. 調査の前提：いま「現参加者の手の内」は直接見えない

- 本ハッカソン（DevOps × AI Agent Hackathon 2026、申込4/27〜**7/10締切**、決勝8/19）は **提出作品ギャラリーが未公開**。現参加者の作品を直接比較するのは構造的に不可能。【確認済み】
- 代理指標として **同系譜の過去ハッカソン受賞作**（Zenn主催 第1〜4回、Google Cloud ADKハッカソン）と **商用市場の既存ツール** を調査した。
- 現参加者の公開シグナルは note 上で散見（後述§5）。**「リリースゲート/DevOps系」と直接バッティングする公開表明は未発見**。【確度中】

---

## 2. 過去受賞作の棚卸し（同系譜ハッカソン）

開催回と受賞作の対応（Zenn/Google Cloud 公式 X で裏取り）【確認済み】:

| 回 | 時期 | 最優秀賞 | 主な上位入賞 |
|---|---|---|---|
| **第1回** | 提出 2024/12〜2025/2、ピッチ 2025/3/13 | **eCOINO**（SCM・需給乖離） | 2位 Manabiya AI（教師負荷）/ 3位 社内のぞき見新聞（社内情報共有） |
| **第2回** | ピッチ 2025/8/5 @ Next Tokyo | **FlatJam**（作曲支援） | 2位 学校だよりAI / 3位 Vibe Planning |
| **第3回** | 提出 2025/8〜9、ピッチ 2025/10/31 | **フクシア**（社会福祉士支援） | 優秀賞5作: PawMate / 添削AI『言の葉』/ RouteKeeperAI / 魔法の天秤 with Gemini / FutureRun |
| **第4回**（Agentic AI） | 提出 2025/12〜2026/2、審査 2026/3/19 | **未発表**（6月時点で審査フェーズ） | — |

> 注: ユーザーが当初「eCOINO/Manabiya が同回」「フクシア最優秀」と認識していたのは正しいが、**回の割り当ては上表が正**（eCOINO=第1回、FlatJam=第2回、フクシア=第3回）。

### 主要作の詳細

- **フクシア（第3回最優秀／本命参照）** — 社会福祉士の業務支援（アセスメント簡易化・支援制度のチャット検索・タスク自動登録）。**ADK＋マルチエージェント**構成と紹介【確度中】。Gemini / Cloud Run。ITに不慣れな福祉職向けの**シンプルUX**を訴求。開発では Gemini CLI / Cline / Codex CLI を `AGENTS.md` 共通形式で併用【確認済み】。
  出典: https://zenn.dev/teritama/articles/aa54b4fbed1231 ／ https://x.com/googlecloud_jp/status/1984232639658643734
- **eCOINO（第1回最優秀）** — サプライチェーンの「計画 vs 現実」のズレを対話型で可視化。**クニエ（QUNIE）のSCMコンサル**が参画した専門家チーム【確認済み】。Gemini対話UIが中核。ADKは時期的に非採用と推測。
  出典: https://x.com/zenn_dev/status/1912339763870462144 ／ https://insight.axc.ne.jp/article/consulnews/4303/
- **Manabiya AI（第1回2位）** — 教師の業務負荷軽減。**LangChain＋Vertex AI＋音声認識のマルチモーダル**（ADKではない点が特徴）。Gemini 2.0 Flash / Firebase / Cloud Run。作業時間 約85%削減を主張【確度中】。
  出典: https://zenn.dev/coco9122/articles/manabiya-ai-coco9122
- **FlatJam（第2回最優秀）** — 作曲プロセスをリアルタイム解析し技法を「セレンディピティ」提示。Flutter / Cloud Run / Gemini / BigQuery / Firestore。
  出典: https://x.com/zenn_dev/status/1952924117386314162

### 受賞作からの観察
- 上位は **福祉・SCM・教育** と「当事者性の強い切実な実課題」に一貫して偏る。
- 技術選定はバラバラ（ADK / LangChain / 素のGemini）で、**技術より「現場の切実さ × 実用UX」が上位の決定因**。
- **DevOps / リリース判定 / コードレビューを主題にした受賞・著名作は表面化せず** → pmz の問題領域はハッカソン内では**空白地帯**に見える。【確度中】

---

## 3. pmz と被る作品はあるか（直接競合の探索）

### ハッカソン作品側：最も近い隣接作 = TrustOps
- **TrustOps / Release Intelligence Control Tower**（Google Cloud **ADKハッカソン**提出、GitLab基盤）
  出典: https://devpost.com/software/trustops
- 「マージリクエストをリリースして安全か」を判定し **approve / review / block** を返す。GitLab Duo（オーケストレーション）＋ Cloud Run/FastAPI の決定論スコアリング ＋ BigQuery履歴 ＋ GitLab CIでの enforcement。【確認済み・スニペット】
- **pmz と同型**: PRマージ前ゲート、3段階出力、履歴を判定に使用、CIにゲート組込み。
- **pmz と違う＝差別化が立つ点**:
  - ✗ **要件充足（PM観点）が無い** — 判定材料はコード/テスト/CI/障害履歴のみ。「PRが要件定義書を満たすか」は見ていない。
  - ✗ **自己改善ループが無い** — 履歴をBigQueryで参照するが、「見逃す→ルール化→検知」で精度が上がる時間軸（Z軸）は説明に出てこない（決定論ルールは静的）。
  - 基盤が GitLab（pmzはGitHub）。

### その他の隣接作（方向性が違う）
- **cd-agent**（自律カナリアデプロイ、Firestoreで過去デプロイから学習）→ デプロイ後運用＝pmzのPhase2領域、PM観点なし。
- **Pipeline Doctor**（CI/CD健全性診断）→ 診断であって可否ゲートではない。
- **SRE Agent（ADK+MCP）**（インシデント対応）→ 事後対応、リリース前ゲートでない。
- **River Reviewer 等コードレビュー系**（Zenn記事群）→ コード品質レビュー、要件充足の可否＋結果学習ではない。

---

## 4. 商用市場での切り分け（新規性の精密化）

凡例: ◯=明確にやる / △=部分的 / ✗=やらない

| ツール | 要件/受け入れ基準の充足判定（PM観点） | Go/No-Go・マージブロック | 障害結果から学習する自己改善 |
|---|---|---|---|
| CodeRabbit | △ linked issue整合は見る | ◯ required check | ✗ 規約/レビュー履歴から学習 |
| Greptile | ✗ | △ | ✗ |
| **Qodo**（Ticket Compliance Agent） | ◯ **Jiraチケットの受入基準でコード充足判定** | ◯ 非充足は自動承認をブロック | △ 受理/却下提案から学習（**障害からではない**） |
| **Atlassian Rovo Dev** | ◯ **acceptance criteria・事業目標に照合** | △ 通知中心 | ✗ |
| GitHub Copilot review | ✗ | ✗ **常にコメント扱い・止めない** | ✗ |
| Graphite Diamond | ✗ | ◯ merge queue | ✗ |
| **Meta Diff Risk Score** | ✗ コード/メタデータのみ | ◯ 上位X%リスクをmerge gate | △ **過去障害ラベルで学習だが静的訓練**（閉ループでない） |
| **ReleaseGate.ai** | ✗ インフラ/運用シグナル中心 | ◯ **auto-approve/flag/block**（条件付き自律そのもの） | ◯ **組織パターンを継続学習**（ただし**デプロイゲート・PM観点なし**） |
| Cortex / OpsLevel | ✗ scorecard基準 | ◯ scorecardでdeploy gate | ✗ |

### 市場の3クラスタと空白
1. **AI PRレビュー系** — コード品質が主眼。学習は「受理された提案/規約」から＝**障害という客観アウトカムからではない**。
2. **デプロイ/変更リスク予測系**（Meta DRS / ReleaseGate.ai / Cortex）— **障害から学習**するが**要件充足を見ない**、多くは**デプロイ段**（PRマージ段でない）。
3. **要件↔実装整合チェック系**（Qodo / Rovo Dev）— **受入基準の充足判定**は pmz と最も重なるが、ソースは Jira/Linear チケットで、**障害からの自己改善ループは持たない**。

### 結論：pmz の独自性（複数要素の交差点）
- 「要件充足のPM判定」も「障害からの学習」も**個別には既存**。だが、
  1. **要件充足判定（Y）と障害アウトカムからの自己改善（Z）を1つのループに統合**した製品は見当たらない。
  2. **要件充足の正解ラベルを客観イベントから自動導出して学習**する設計は前例なし（既存は「受理レビュー提案」依存＝確証バイアス源）。pmz の §3.3.1（自己生成ラベルで学習しない）は質的に厳格。
  3. **「要件未達」を障害とは別軸（最長30日の遅延確定）で学習対象にする**非対称設計は調査範囲のどの製品にもない。
  4. **決定論的ハードガード＋3値（満たす/満たさない/検証不能）＋棄権エスカレーション**を要件充足判定に適用する例は見当たらない。

> 一行: pmz の新規性は**個別機能ではなく、X(エンジニアリング)×Y(PM/要件)×Z(障害結果からの学習) の交差点と、客観ラベルで要件未達まで学習する点**にある。
> **最も直接的な競合は ReleaseGate.ai**（条件付き自律＋学習が近い）。差別化は (a)PRマージ段 (b)要件定義書ベースのPM判定 (c)要件未達の遅延学習。

出典: TrustOps https://devpost.com/software/trustops ／ Qodo https://docs.qodo.ai/qodo-documentation/code-review/qodo-merge/features/custom-compliance ／ Rovo Dev https://www.atlassian.com/software/rovo-dev/code-review ／ Meta DRS https://engineering.fb.com/2025/08/06/developer-tools/diff-risk-score-drs-ai-risk-aware-software-development-meta/ ／ ReleaseGate.ai https://www.releasegate.ai/ ／ Copilot https://docs.github.com/copilot/using-github-copilot/code-review/using-copilot-code-review

---

## 5. 本ハッカソン2026 特有の傾向と現参加者シグナル

### 公式3本柱「つくる・まわす・とどける」原文【確認済み・公式ブログ全文】
- **つくる**: Gemini中核で「実務で役立つ独創的なAIエージェントを設計・実装」。アイデアの面白さだけでなく**エージェントとしての必然性・自律的に判断しタスクを実行する設計まで踏み込んで評価**。
- **まわす**: 「CI/CDなど DevOps のフローを構築し、**AIを継続的に改善するサイクルを参加者自身が回す**。机上の理論ではなく実装して動かす」。
- **とどける**: Google Cloudへのデプロイで「スケーラブルな環境で**本番品質**のプロダクトを届ける。**動くものをつくる、ではなく、届くものをつくる**」。

出典: https://cloud.google.com/blog/ja/products/ai-machine-learning/devops-ai-agent-hackathon-2026?hl=ja

### 技術要件
- **必須**: Gemini ／ Gemini Enterprise Agent Platform。【確認済み】
- **強く推奨（ブートキャンプ対象）**: ADK / Cloud Run / Gemini API。**ただし公式ブログ本文では Cloud Run・ADK を"必須"と明示していない**（推奨レベルと解釈が安全）。【確度中】
- **DORA / Four Keys**: 公式ブログに**明示言及なし**【確認済み・否定】。→ pmz が DORA に踏み込むのは「自発的な上積み」であって必須充足ではない。MVPで Phase2 送りにした判断と矛盾しない。
- **前回（第4回）との違い**: 第4回は純粋な Agentic AI で **DevOps/CI/CD言及なし＝"作る"止まり**。今回は「まわす（CI/CD・継続改善）」「とどける（本番デプロイ・スケーラビリティ）」を足し、運用・本番品質まで評価対象に拡張。主催も Zenn系→**Findy**（開発生産性に強い）に交代。

### スケジュール【確認済み・複数一致】
申込 4/27〜7/10 ／ ブートキャンプ 6/1〜6/12 ／ 提出締切 7/10 ／ ファイナリスト発表 7/30 ／ 決勝 8/19（Google渋谷・10組ピッチ）。賞金総額200万円。18歳以上・国内在住、個人/チーム可。

### 現参加者の公開シグナル【確認済み】
- **Ryo（note: goro9426）** — 「ITほぼ素人の化学エンジニアが夏のAIエージェントハッカソンに一人で挑む」。**ソロ・初心者**、化学業界向けAI業務効率化を志向。週次note連載予定。 https://note.com/goro9426/n/n7c1ec4883ae2
- **Ryoma Takamura（note）** — 参加表明＋「note を読んだ別エンジニアも参加」という連鎖。note上でコミュニティ形成の兆し。 https://note.com/ryoma_takamura/n/n379acc8f4e78
- 観察: 現時点の公開シグナルは「**個人・初心者・ソロ参加の表明**」が目立ち、**DevOps/開発生産性系の尖った競合は未捕捉**。pmz のDevOpsど真ん中×PM観点という尖りは現状希少に見える【推測】。

---

## 6. 勝ち筋（審査傾向）と pmz への示唆

### 審査の構造【確認済み（複数二次情報一致）】
3軸: ①アイデアの質（独創性）②課題の明確さと解決策の有効性 ③実現（拡張可能・運用可能・コスト効率）。配点は明示なしだが均等運用とされる。「AIをどう使ったか」より「**どんな価値を提供できるか**」を重視。

### 受賞作の共通項【確認済み】
- **課題の切実さ・社会性が最重要**（福祉/SCM/教育）。実ワークフローに基づく実用的解決策。
- **本番志向アーキ**（拡張性）。**UXの作り込み**（Flutter/Three.js等）。**ドメイン専門性**（eCOINO=SCMコンサル、フクシア=福祉）。
- **マルチエージェント/ADK は「使えば加点」でなく「本番課題に必然性をもって使う」のが受賞条件**（ADKハッカソン公式が明言）。
- **Gemini/Vertex AI は事実上の前提**（第1回は全上位入賞がVertex AI＋Gemini活用）。
- **Zenn提出記事の質**が露出・一次審査の土台。受賞者は「受賞戦略」を記事で言語化している。

### pmz への実務的示唆
1. **課題の切実さを先頭に**。技術説明から入らず「リリース判断の属人性・障害見落とし」を審査員が一発で理解できる形に。
2. **「まわす＝自己改善ループ」が2026の明示加点軸** → §3.3 の「見逃す→学習→検知」デモはテーマ直撃。§8.1の「死守＝自己改善が見えるデモ」は審査傾向と整合。
3. **エージェントの必然性・自律判断設計**を公式が踏み込み評価 → 「条件付き自律＋決定論的ハードガード」を必然性の論拠として前面に。
4. **新規性の言語化を補正**: 「PM観点判定そのもの」は Qodo/Rovo Dev が出荷済み。ピッチでは **「要件充足を障害アウトカムで自己改善する統合ループ（X×Y×Z）」と「要件未達の遅延学習」** を新規性の核に据え、TrustOps的CIゲート・ReleaseGate.ai との差分を**先回りで明示**して"既出感"を防ぐ。
5. **山田裕一朗（Findy代表）＝DevOps/開発生産性が本丸** → pmz の「DevOpsを回す＋自分自身もDevOpsで改善される二重構造」は刺さりやすい【推測（強）】。

---

## 7. 未確認・継続ウォッチ項目

- **DevOps 2026 の正式な審査員リストと配点** — Findy/connpass/prtimes が 403 で未確定（中井悦司・佐藤一憲・山田裕一朗・佐藤将高・吉川大央は妥当だが裏取り未完）。
- **Cloud Run / ADK の必須/任意の最終判定**、提出物の必須要件（デモ動画の長さ等）。
- **提出締切（7/10）後の作品ギャラリー** — 同回はDevOpsテーマゆえ被りリスクが他回より高い。公開後に再調査推奨。
- **TrustOps / ReleaseGate.ai / Qodo / Meta DRS** の原文精読（403回避手段で）。「障害からの学習の有無」「要件充足の不在」は新規性主張に直結するため提出前に再確認。
- ハッシュタグ `#gcai_agent` 等での DevOps系作品シグナルの継続監視。

---

## 主要ソース一覧

- Google Cloud 公式ブログ（DevOps 2026・全文取得）: https://cloud.google.com/blog/ja/products/ai-machine-learning/devops-ai-agent-hackathon-2026?hl=ja
- Google Cloud 公式ブログ（ADKハッカソン受賞・全文取得）: https://cloud.google.com/blog/ja/products/ai-machine-learning/adk-hackathon-results-winners-and-highlights?hl=ja
- 第4回告知: https://cloud.google.com/blog/ja/products/ai-machine-learning/the-4th-agentic-ai-hackathon-is-now-accepting-participants
- 受賞告知（Zenn/Google Cloud 公式X）: 第1回 https://x.com/zenn_dev/status/1912339763870462144 ／ 第2回 https://x.com/zenn_dev/status/1952924117386314162 ／ 第3回 https://x.com/zenn_dev/status/1985636901290983533 ・ https://x.com/googlecloud_jp/status/1984232639658643734
- 受賞作記事: フクシア https://zenn.dev/teritama/articles/aa54b4fbed1231 ／ Manabiya AI https://zenn.dev/coco9122/articles/manabiya-ai-coco9122 ／ eCOINO（クニエ） https://insight.axc.ne.jp/article/consulnews/4303/
- 隣接作: TrustOps https://devpost.com/software/trustops ／ ADKハッカソン作品 https://github.com/shubhamprajapati7748/google-adk-apps
- 商用競合: Qodo https://www.qodo.ai/blog/qodo-ai-code-review-platform/ ／ Rovo Dev https://www.atlassian.com/software/rovo-dev/code-review ／ Meta DRS https://engineering.fb.com/2025/08/06/developer-tools/diff-risk-score-drs-ai-risk-aware-software-development-meta/ ／ ReleaseGate.ai https://www.releasegate.ai/ ／ CodeRabbit https://docs.coderabbit.ai/pr-reviews/coderabbit-review
- 審査傾向（二次）: issoh https://www.issoh.co.jp/tech/details/8946/ ／ 第1回振り返り https://zenn.dev/taku_sid/articles/20250403_ai_hackathon_review ／ 受賞戦略 https://zenn.dev/kikagaku/articles/d2876e8e2e50a5 ／ Devpostルール https://googlecloudjapanaihackathon.devpost.com/details/rulesinjapanese
- 現参加者シグナル: https://note.com/goro9426/n/n7c1ec4883ae2 ／ https://note.com/ryoma_takamura/n/n379acc8f4e78
- 本ハッカソン connpass（要確認・403）: https://findy-tools.connpass.com/event/392105/
