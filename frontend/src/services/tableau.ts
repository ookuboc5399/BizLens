declare global {
  interface Window {
    tableau: any;
  }
}

interface TableauConfig {
  url: string;
  hideTabs?: boolean;
  hideToolbar?: boolean;
  width?: string;
  height?: string;
}

export class TableauService {
  private static readonly BASE_URL = import.meta.env.VITE_TABLEAU_URL;
  private static readonly VIEW_NAME = import.meta.env.VITE_TABLEAU_VIEW;

  private static createViz(containerId: string, config: TableauConfig): Promise<any> {
    return new Promise((resolve, reject) => {
      try {
        const container = document.getElementById(containerId);
        if (!container) {
          throw new Error(`Container element ${containerId} not found`);
        }

        // Clear any existing content
        container.innerHTML = '';

        const options = {
          hideTabs: config.hideTabs ?? true,
          hideToolbar: config.hideToolbar ?? true,
          width: config.width ?? '100%',
          height: config.height ?? '600px',
          onFirstInteractive: () => {
            resolve(viz);
          }
        };

        const viz = new window.tableau.Viz(container, config.url, options);
      } catch (error) {
        reject(error);
      }
    });
  }

  static async mountCompanyOverview(containerId: string, companyId: string): Promise<void> {
    const url = `${this.BASE_URL}/${this.VIEW_NAME}/overview?:embed=y&Company=${companyId}`;
    await this.createViz(containerId, {
      url,
      hideTabs: true,
    });
  }

  static async mountValuation(containerId: string, companyId: string): Promise<void> {
    const url = `${this.BASE_URL}/${this.VIEW_NAME}/valuation?:embed=y&Company=${companyId}`;
    await this.createViz(containerId, {
      url,
      hideTabs: true,
    });
  }

  static async mountProfit(containerId: string, companyId: string): Promise<void> {
    const url = `${this.BASE_URL}/${this.VIEW_NAME}/profit?:embed=y&Company=${companyId}`;
    await this.createViz(containerId, {
      url,
      hideTabs: true,
    });
  }

  static async mountBalance(containerId: string, companyId: string): Promise<void> {
    const url = `${this.BASE_URL}/${this.VIEW_NAME}/balance?:embed=y&Company=${companyId}`;
    await this.createViz(containerId, {
      url,
      hideTabs: true,
    });
  }
}
