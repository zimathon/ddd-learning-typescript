# DDD Learning TypeScript

ドメイン駆動設計（DDD）を段階的に学習するためのTypeScriptリポジトリです。

## 概要

このリポジトリは、DDDの主要な概念とパターンを実践的に学ぶことを目的としています。小規模ECサイトをサンプルドメインとして、ステップバイステップでDDDの各要素を理解し、実装していきます。

## 学習ステップ

- **Step 0**: 環境セットアップとDDD用語の基礎
- **Step 1**: Value ObjectとEntityの基本
- **Step 2**: AggregateとRepositoryパターン
- **Step 3**: Domain ServiceとApplication Service
- **Step 4**: Domain Eventとイベント駆動アーキテクチャ
- **Step 5**: 境界づけられたコンテキストとマイクロサービス（発展）

## 技術スタック

- **言語**: TypeScript 5.x
- **ランタイム**: Node.js 20.x
- **テスト**: Jest
- **リンター**: ESLint, Prettier
- **ビルドツール**: tsx, tsc

## セットアップ

```bash
# 依存関係のインストール
npm install

# 開発環境の起動
npm run dev

# テストの実行
npm test

# ビルド
npm run build
```

## ディレクトリ構成

```
.
├── docs/                    # ドキュメント・ADR・用語集
├── step-0-setup/           # 環境セットアップと基礎知識
├── step-1-basic-model/     # Entity/Value Objectの基本
├── step-2-aggregate-repo/  # Aggregate/Repositoryパターン
├── step-3-services/        # Domain/Application Service
├── step-4-events/          # Domain Eventとイベント駆動
└── step-5-advanced/        # 発展的なトピック
```

## 学習の進め方

1. まず`docs/00_overview.md`を読んでDDDの全体像を把握する
2. `step-0-setup`で環境構築と基本用語を理解する
3. 各ステップを順番に進める（各ステップには独立したREADMEと演習課題があります）
4. `docs/exercises/`にある課題に取り組む
5. 実装が終わったらテストを書いて理解を深める

## サンプルドメイン

**小規模ECサイト**を題材として、以下の概念を実装していきます：

- 顧客（Customer）
- 商品（Product）
- 注文（Order）
- 在庫（Inventory）
- 支払い（Payment）

## 主要なDDDパターン

このリポジトリで学べるパターン：

- ✅ Entity（エンティティ）
- ✅ Value Object（値オブジェクト）
- ✅ Aggregate（集約）
- ✅ Repository（リポジトリ）
- ✅ Domain Service（ドメインサービス）
- ✅ Application Service（アプリケーションサービス）
- ✅ Domain Event（ドメインイベント）
- ✅ Specification（仕様）
- ✅ Factory（ファクトリ）

## 参考資料

- エリック・エヴァンス『ドメイン駆動設計』
- ヴァーノン・ヴォーン『実践ドメイン駆動設計』
- 成瀬允宣『ドメイン駆動設計入門』

## ライセンス

MIT