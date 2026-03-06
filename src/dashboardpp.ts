import { App, Modal, Notice, TFile, TFolder } from 'obsidian';
import { exec } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';
import DNPlugin from './main';
import { DNConfirmModal } from './modals/dnconfirmmodal';

interface ScriptRegistryEntry {
	id: string;
	name: string;
	type: string;
	description: string;
	command?: string;
	script_path?: string;
	tags: string[];
	safety: 'safe' | 'unsafe';
}

interface ContextRule {
	folder?: string;
	include_tags?: string[];
	exclude_tags?: string[];
	include_scripts?: string[];
	exclude_scripts?: string[];
}

interface ContextRulesDocument {
	default_include_tags?: string[];
	default_exclude_tags?: string[];
	rules?: ContextRule[];
}

function normalizeTags(tags: unknown): string[] {
	if (!Array.isArray(tags)) {
		return [];
	}
	return tags.filter((tag): tag is string => typeof tag === 'string').map((tag) => tag.toLowerCase());
}

function isUnsafeScript(script: ScriptRegistryEntry): boolean {
	if (script.safety === 'unsafe') {
		return true;
	}
	const destructiveTags = new Set(['unsafe', 'destructive', 'delete', 'remove', 'rm']);
	return script.tags.some((tag) => destructiveTags.has(tag));
}

export class DashboardGenerator {
	constructor(private app: App, private plugin: DNPlugin) { }

	private folderDepth(folderPath: string): number {
		if (!folderPath) {
			return 0;
		}
		return folderPath.split('/').filter((segment) => segment.length > 0).length;
	}

	private isIgnored(folderPath: string): boolean {
		if (!folderPath) {
			return false;
		}
		const ignored = this.plugin.settings.dashboardpp_ignore_folders
			.split(',')
			.map((item) => item.trim())
			.filter((item) => item.length > 0);
		return ignored.some((entry) => folderPath === entry || folderPath.startsWith(`${entry}/`));
	}

	private dashboardPathForFolder(folderPath: string): string {
		const prefix = this.plugin.settings.dashboardpp_filename_prefix || 'DB_';
		if (!folderPath) {
			return `${prefix}HOME.md`;
		}
		const normalized = folderPath.replace(/[^a-zA-Z0-9/_-]/g, '_').replace(/\//g, '_').toUpperCase();
		return `${prefix}${normalized}.md`;
	}

	private extractManualSection(content: string): string {
		const regex = /<!-- MANUAL:START -->([\s\S]*?)<!-- MANUAL:END -->/m;
		const match = content.match(regex);
		if (!match) {
			return '\n- Add your manual notes here.\n';
		}
		return match[1];
	}

	private buildDashboardContent(folderPath: string, manualSection: string): string {
		const folder = folderPath || '/';
		const parent = folderPath.includes('/') ? this.dashboardPathForFolder(folderPath.split('/').slice(0, -1).join('/')) : this.dashboardPathForFolder('');
		const root = this.dashboardPathForFolder('');
		const lastGenerated = new Date().toISOString().slice(0, 10);

		const children = this.app.vault.getAllLoadedFiles()
			.filter((item): item is TFolder => item instanceof TFolder)
			.filter((item) => (folderPath ? item.path.startsWith(`${folderPath}/`) : item.path.length > 0))
			.filter((item) => this.folderDepth(item.path) === this.folderDepth(folderPath) + 1)
			.filter((item) => !this.isIgnored(item.path))
			.sort((a, b) => a.path.localeCompare(b.path));

		const childLinks = children.length > 0
			? children.map((child) => `- [[${this.dashboardPathForFolder(child.path).replace(/\.md$/, '')}|${child.name} Dashboard]]`).join('\n')
			: '- No child folders in scope.';

		const files = this.app.vault.getMarkdownFiles()
			.filter((file) => {
				if (!folderPath) {
					return !file.path.includes('/');
				}
				return path.posix.dirname(file.path) === folderPath;
			})
			.sort((a, b) => a.path.localeCompare(b.path));

		const fileLinks = files.length > 0
			? files.map((file) => `- [[${file.path}]]`).join('\n')
			: '- No notes found in this folder.';

		return `---\ntype: dashboard\nscope: folder\nfolder_path: ${folder}\nparent_dashboard: ${parent}\nroot_dashboard: ${root}\nstatus: active\nlast_generated: ${lastGenerated}\n---\n\n# Dashboard: ${folder}\n\n<!-- AUTO:START -->\n## Child Dashboards\n${childLinks}\n\n## Notes In Folder\n${fileLinks}\n<!-- AUTO:END -->\n\n<!-- MANUAL:START -->${manualSection}<!-- MANUAL:END -->\n`;
	}

	private async upsertDashboard(folderPath: string): Promise<string> {
		const dashboardPath = this.dashboardPathForFolder(folderPath);
		const existing = this.app.vault.getAbstractFileByPath(dashboardPath);
		let manualSection = '\n- Add your manual notes here.\n';
		if (existing instanceof TFile) {
			manualSection = this.extractManualSection(await this.app.vault.read(existing));
		}
		const content = this.buildDashboardContent(folderPath, manualSection);
		if (existing instanceof TFile) {
			await this.app.vault.modify(existing, content);
		} else {
			await this.app.vault.create(dashboardPath, content);
		}
		return dashboardPath;
	}

	private async ensureIndexFile(folder: TFolder): Promise<void> {
		if (!folder.path) {
			return;
		}
		const indexPath = `${folder.path}/INDEX.md`;
		if (this.app.vault.getAbstractFileByPath(indexPath)) {
			return;
		}
		const content = `# Index: ${folder.name}\n\n- [[${this.dashboardPathForFolder(folder.path).replace(/\.md$/, '')}|Folder Dashboard]]\n`;
		await this.app.vault.create(indexPath, content);
	}

	async generateAllDashboards(): Promise<string[]> {
		const folders = this.app.vault.getAllLoadedFiles()
			.filter((item): item is TFolder => item instanceof TFolder)
			.filter((item) => this.folderDepth(item.path) <= this.plugin.settings.dashboardpp_max_depth)
			.filter((item) => !this.isIgnored(item.path))
			.sort((a, b) => a.path.localeCompare(b.path));

		const generated: string[] = [];
		generated.push(await this.upsertDashboard(''));
		for (const folder of folders) {
			if (!folder.path) {
				continue;
			}
			generated.push(await this.upsertDashboard(folder.path));
			await this.ensureIndexFile(folder);
		}
		return generated;
	}

	async openCurrentFolderDashboard(): Promise<void> {
		const folderPath = this.plugin.getCurrentFolderPath();
		const dashboardPath = await this.upsertDashboard(folderPath);
		const file = this.app.vault.getAbstractFileByPath(dashboardPath);
		if (file instanceof TFile) {
			await this.app.workspace.getLeaf(true).openFile(file);
		}
	}
}

export class ScriptExecutionService {
	constructor(private app: App, private plugin: DNPlugin) { }


	private getVaultBasePath(): string {
		const adapter = this.app.vault.adapter as { getBasePath?: () => string };
		return adapter.getBasePath ? adapter.getBasePath() : '';
	}

	private async readJsonFile<T>(filePath: string): Promise<T | null> {
		try {
			const content = await fs.readFile(filePath, 'utf8');
			return JSON.parse(content) as T;
		} catch {
			return null;
		}
	}

	private normalizeRegistry(data: unknown): ScriptRegistryEntry[] {
		const scripts = Array.isArray(data) ? data : (data as { scripts?: unknown })?.scripts;
		if (!Array.isArray(scripts)) {
			return [];
		}
		return scripts
			.map((item) => {
				if (!item || typeof item !== 'object') {
					return null;
				}
				const row = item as Record<string, unknown>;
				const id = String(row.id || row.name || '');
				if (!id) {
					return null;
				}
				return {
					id,
					name: String(row.name || id),
					type: String(row.type || 'shell'),
					description: String(row.description || ''),
					command: typeof row.command === 'string' ? row.command : undefined,
					script_path: typeof row.script_path === 'string' ? row.script_path : undefined,
					tags: normalizeTags(row.tags),
					safety: row.safety === 'unsafe' ? 'unsafe' : 'safe'
				} as ScriptRegistryEntry;
			})
			.filter((item): item is ScriptRegistryEntry => item !== null);
	}

	private getApplicableRule(rulesDoc: ContextRulesDocument, folderPath: string): ContextRule | null {
		const rules = rulesDoc.rules || [];
		let best: ContextRule | null = null;
		let bestLen = -1;
		for (const rule of rules) {
			const folder = rule.folder || '';
			if (!folder) {
				continue;
			}
			if (folderPath === folder || folderPath.startsWith(`${folder}/`)) {
				if (folder.length > bestLen) {
					best = rule;
					bestLen = folder.length;
				}
			}
		}
		return best;
	}

	async getScriptsForFolder(folderPath: string): Promise<ScriptRegistryEntry[]> {
		const registryDoc = await this.readJsonFile<unknown>(this.plugin.settings.dashboardpp_script_registry_path);
		const rulesDoc = await this.readJsonFile<ContextRulesDocument>(this.plugin.settings.dashboardpp_context_rules_path) || {};
		const scripts = this.normalizeRegistry(registryDoc);
		const rule = this.getApplicableRule(rulesDoc, folderPath);
		const includeTags = new Set([...(rulesDoc.default_include_tags || []), ...(rule?.include_tags || [])].map((tag) => tag.toLowerCase()));
		const excludeTags = new Set([...(rulesDoc.default_exclude_tags || []), ...(rule?.exclude_tags || [])].map((tag) => tag.toLowerCase()));
		const includeScripts = new Set((rule?.include_scripts || []));
		const excludeScripts = new Set((rule?.exclude_scripts || []));

		return scripts.filter((script) => {
			if (this.plugin.settings.dashboardpp_only_safe_scripts && isUnsafeScript(script)) {
				return false;
			}
			if (excludeScripts.has(script.id)) {
				return false;
			}
			if (includeScripts.size > 0 && !includeScripts.has(script.id)) {
				return false;
			}
			if (excludeTags.size > 0 && script.tags.some((tag) => excludeTags.has(tag))) {
				return false;
			}
			if (includeTags.size > 0 && !script.tags.some((tag) => includeTags.has(tag))) {
				return false;
			}
			return true;
		});
	}

	private buildCommand(script: ScriptRegistryEntry): string {
		if (script.command) {
			return script.command;
		}
		if (!script.script_path) {
			return '';
		}
		if (script.type === 'python') {
			return `python "${script.script_path}"`;
		}
		if (script.type === 'powershell') {
			return `powershell -ExecutionPolicy Bypass -File "${script.script_path}"`;
		}
		if (script.type === 'bat' || script.type === 'cmd') {
			return `cmd /c "${script.script_path}"`;
		}
		return `"${script.script_path}"`;
	}

	private async appendLog(entry: string): Promise<void> {
		const logPath = this.plugin.settings.dashboardpp_log_path;
		await fs.mkdir(path.dirname(logPath), { recursive: true });
		await fs.appendFile(logPath, `${entry}\n`, 'utf8');
	}

	async runScript(script: ScriptRegistryEntry, folderPath: string): Promise<void> {
		if (!this.plugin.settings.dashboardpp_enable_script_execution) {
			new Notice('Dashboard++ script execution is disabled in settings.');
			return;
		}
		if (isUnsafeScript(script)) {
			const confirm = new DNConfirmModal(this.app, 'Unsafe script confirmation', `The script "${script.name}" is marked unsafe. Continue?`, 'Run unsafe script', 'mod-warning');
			confirm.open();
			const accepted = await confirm.resultPromise;
			if (!accepted) {
				new Notice('Unsafe script run cancelled.');
				return;
			}
		}

		const command = this.buildCommand(script);
		if (!command) {
			new Notice('Script has no runnable command or script path.');
			return;
		}
		const start = Date.now();
		let status = 'success';
		let stderrSnippet = '';
		try {
			await new Promise<void>((resolve, reject) => {
				exec(command, { cwd: this.getVaultBasePath() }, (error, _stdout, stderr) => {
					if (stderr) {
						stderrSnippet = stderr.slice(0, 180).replace(/\n/g, ' ');
					}
					if (error) {
						reject(error);
						return;
					}
					resolve();
				});
			});
			new Notice(`Script completed: ${script.name}`);
		} catch {
			status = 'failed';
			new Notice(`Script failed: ${script.name}`);
		}
		const duration = Date.now() - start;
		const line = JSON.stringify({
			timestamp: new Date().toISOString(),
			folder: folderPath,
			script_id: script.id,
			command,
			status,
			duration_ms: duration,
			stderr: stderrSnippet
		});
		try {
			await this.appendLog(line);
		} catch {
			new Notice('Unable to write Dashboard++ run log.');
		}
	}

	async copyCommand(script: ScriptRegistryEntry): Promise<void> {
		const command = this.buildCommand(script);
		if (!command) {
			new Notice('No command to copy for this script.');
			return;
		}
		await navigator.clipboard.writeText(command);
		new Notice('Command copied to clipboard.');
	}

	async openScriptFile(script: ScriptRegistryEntry): Promise<void> {
		if (!script.script_path) {
			new Notice('No script file path available.');
			return;
		}
		const base = this.getVaultBasePath();
		const candidate = script.script_path.replace(/\\/g, '/');
		const relativePath = candidate.startsWith(base.replace(/\\/g, '/'))
			? candidate.slice(base.length + 1)
			: candidate;
		const file = this.app.vault.getAbstractFileByPath(relativePath);
		if (file instanceof TFile) {
			await this.app.workspace.getLeaf(true).openFile(file);
			return;
		}
		new Notice(`Script path: ${script.script_path}`);
	}
}

export class DashboardScriptPanelModal extends Modal {
	constructor(
		app: App,
		private service: ScriptExecutionService,
		private folderPath: string
	) {
		super(app);
	}

	async onOpen() {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.createEl('h2', { text: `Dashboard++ Scripts (${this.folderPath || '/'})` });
		const scripts = await this.service.getScriptsForFolder(this.folderPath);
		if (scripts.length === 0) {
			contentEl.createEl('p', { text: 'No scripts match this folder context.' });
			return;
		}
		for (const script of scripts) {
			const card = contentEl.createEl('div', { cls: 'dashboardpp-script-card' });
			card.createEl('h3', { text: script.name });
			card.createEl('p', { text: `${script.description || 'No description'} (${script.type})` });
			card.createEl('p', { text: `Safety: ${isUnsafeScript(script) ? 'unsafe' : 'safe'}` });
			const actions = card.createEl('div', { cls: 'dashboardpp-script-actions' });

			actions.createEl('button', { text: 'Run' }).onclick = async () => {
				await this.service.runScript(script, this.folderPath);
			};
			actions.createEl('button', { text: 'Copy command' }).onclick = async () => {
				await this.service.copyCommand(script);
			};
			actions.createEl('button', { text: 'Open script file' }).onclick = async () => {
				await this.service.openScriptFile(script);
			};
		}
	}

	onClose() {
		this.contentEl.empty();
	}
}
