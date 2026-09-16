CREATE TABLE `intake_clock` (
	`id` text PRIMARY KEY NOT NULL,
	`last_started` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `analysis_jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`arxiv` text NOT NULL,
	`status` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	`source_key` text,
	`result_key` text,
	`error_code` text,
	`error_message` text,
	`analysis_id` text,
	`parent_id` text,
	`revision` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE INDEX `analysis_jobs_status_updated` ON `analysis_jobs` (`status`,`updated_at`);