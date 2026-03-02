# Temporal OMS Web UI

A modern, responsive web interface for the Temporal Order Management System built with SvelteKit, TypeScript, and TailwindCSS.

## Overview

This is a SvelteKit-based single-page application (SPA) that provides a UI for interacting with the Temporal OMS microservices (Apps, Processing, and Risk domains). The UI is built with:

- **SvelteKit 2.9.0**: Modern reactive framework for building web apps
- **Svelte 5.2.11**: Lightweight, compiler-based UI framework
- **TypeScript 5.7.2**: Type-safe JavaScript
- **TailwindCSS 3.4.17**: Utility-first CSS framework
- **Vite 5.4.11**: Next generation build tool with fast HMR

## Prerequisites

- **Node.js**: 18+ (verified with Node 22.x)
- **npm**: 8+ (comes with Node.js)

## Getting Started

### Installation

```bash
cd web
npm install
```

### Development Server

Run the development server with hot module replacement (HMR):

```bash
npm run dev
```

The UI will be available at `http://localhost:5173` (or the next available port if 5173 is in use).

Development mode provides:
- Instant hot reload on file changes
- Full source maps for debugging
- TypeScript checking via Svelte Check

### Build for Production

Create an optimized production build:

```bash
npm run build
```

This generates a production-ready application in the `.svelte-kit/output` directory.

### Preview Production Build

After building, preview the production bundle locally:

```bash
npm run preview
```

This runs a preview server on `http://localhost:4173`.

## Available Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Start development server with HMR |
| `npm run build` | Create production build |
| `npm run preview` | Preview production build locally |
| `npm run check` | Type-check and lint Svelte components |
| `npm run check:watch` | Watch mode for type-checking |
| `npm run lint` | Run ESLint on code |

## Project Structure

```
web/
├── src/
│   ├── routes/           # SvelteKit page routes
│   ├── lib/              # Reusable components and utilities
│   ├── app.svelte        # Root component
│   └── app.css           # Global styles
├── static/               # Static assets (images, fonts, etc.)
├── .svelte-kit/          # SvelteKit build output (gitignored)
├── svelte.config.js      # SvelteKit configuration
├── tailwind.config.js    # TailwindCSS configuration
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite build configuration
└── package.json          # Project dependencies
```

## Environment Configuration

The UI communicates with backend microservices. Configure API endpoints via environment variables:

```bash
# Example: .env.local (create this file in the web directory)
VITE_APPS_API_URL=http://localhost:8080
VITE_PROCESSING_API_URL=http://localhost:8081
VITE_RISK_API_URL=http://localhost:8082
```

Any environment variables prefixed with `VITE_` are accessible in the client-side code via `import.meta.env.VITE_*`.

## Deployment

### Docker Deployment

The project includes a `Dockerfile` for containerized deployment:

```bash
# Build Docker image
docker build -t temporal-oms-web:latest .

# Run container
docker run -p 3000:3000 temporal-oms-web:latest
```

### Node Adapter

The project uses the `@sveltejs/adapter-node` for Node.js deployment. To deploy:

1. Build the application: `npm run build`
2. Install production dependencies: `npm ci --only=production`
3. Run with Node.js: `node build/index.js`

## Connecting to Backend Services

### Available Services

The web UI connects to three main microservices:

| Service | Port | API Base |
|---------|------|----------|
| Apps API | 8080 | `/api/v1/apps/*` |
| Processing API | 8081 | `/api/v1/processing/*` |
| Risk API | 8082 | `/api/v1/risk/*` |

### Starting Backend Services

Ensure the backend microservices are running before using the UI:

```bash
# From the java directory
cd ../java

# Start all microservices
mvn spring-boot:run -rf :apps-api  # Terminal 1
mvn spring-boot:run -rf :processing-api  # Terminal 2
mvn spring-boot:run -rf :risk-api  # Terminal 3
```

Or run each API module individually:

```bash
# Apps API
java -jar apps/apps-api/target/apps-api-1.0.0-SNAPSHOT.jar

# Processing API
java -jar processing/processing-api/target/processing-api-1.0.0-SNAPSHOT.jar

# Risk API
java -jar risk/risk-api/target/risk-api-1.0.0-SNAPSHOT.jar
```

## Development Workflow

### Type Checking

Run Svelte type checking:

```bash
npm run check
```

Or watch for changes:

```bash
npm run check:watch
```

### Linting

Check code style with ESLint:

```bash
npm run lint
```

### Hot Module Replacement (HMR)

During development, changes to Svelte components, styles, and scripts are automatically reflected in the browser without full page reloads.

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Troubleshooting

### Port Already in Use

If port 5173 is already in use, Vite will automatically use the next available port. Check the terminal output for the actual URL.

### CORS Issues

If you see CORS errors when calling backend APIs, ensure:
1. Backend services are running on the correct ports
2. Backend services have CORS enabled
3. Environment variables point to correct API endpoints

### Module Not Found Errors

Clear the cache and reinstall:

```bash
rm -rf node_modules package-lock.json .svelte-kit
npm install
```

### Build Issues

Verify Node.js version compatibility:

```bash
node --version  # Should be 18+
npm --version   # Should be 8+
```

## Performance

The UI is optimized for performance:

- **Code splitting**: Routes are automatically split and lazy-loaded
- **Tree-shaking**: Unused code is removed during build
- **Minification**: Production build is minified
- **Asset optimization**: Images and fonts are optimized

## Additional Resources

- [SvelteKit Documentation](https://kit.svelte.dev)
- [Svelte Documentation](https://svelte.dev)
- [TailwindCSS Documentation](https://tailwindcss.com)
- [Vite Documentation](https://vitejs.dev)

## License

Same as the parent Temporal OMS project.

---

*For backend development and Java microservices, see the [Java README](../java/README.md) if available.*