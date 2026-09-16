import { integer, sqliteTable, text, index } from 'drizzle-orm/sqlite-core';

export const jobs = sqliteTable('analysis_jobs', {
  id: text('id').primaryKey(),
  arxiv: text('arxiv').notNull(),
  status: text('status').notNull(),
  createdAt: text('created_at').notNull(),
  updatedAt: text('updated_at').notNull(),
  sourceKey: text('source_key'),
  resultKey: text('result_key'),
  errorCode: text('error_code'),
  errorMessage: text('error_message'),
  analysisId: text('analysis_id'),
  parentId: text('parent_id'),
  revision: integer('revision').notNull().default(0),
}, (table) => [index('analysis_jobs_status_updated').on(table.status, table.updatedAt)]);

export const intakeClock = sqliteTable('intake_clock', {
  id: text('id').primaryKey(),
  lastStarted: integer('last_started').notNull(),
});
