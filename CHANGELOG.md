# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Java 21 Support Configuration

#### Summary
Successfully configured the entire project to compile and run with Java 21.0.2 using the latest stable versions of all major dependencies as of January 2025.

#### Key Changes

**Java & Maven Configuration**
- Target Java Version: 21
- Maven Version: 3.9.9+
- Maven Compiler Plugin: 3.14.1
  - Explicitly declares `plexus-compiler-javac:2.16.1` as a dependency (critical for Java 21 support)
  - Configuration: `fork=true` with explicit javac executable path
  - Uses `source=21` and `target=21` settings

**Critical Fix for Java 21**
The Maven compiler plugin's default plexus-compiler-javac (version 2.15.0) does not recognize Java 21 as a valid target release. Solution:
- Upgrade to `maven-compiler-plugin:3.14.1`
- Explicitly declare `plexus-compiler-javac:2.16.1` as a plugin dependency
- Enable fork mode and point to the system javac executable
- This allows Maven to use the actual Java 21 javac compiler instead of the older embedded version

#### Jackson Dependency Resolution

**Important**: Spring Boot 4.0.2 specifies Jackson 2.20.2 through its BOM (Bill of Materials). Do NOT override this to a different major version (e.g., 2.21.0 or 3.x). Mixing Jackson versions on the classpath causes `NoClassDefFoundError: com/fasterxml/jackson/annotation/JsonSerializeAs` at runtime. Always use the Jackson version managed by Spring Boot's BOM for compatibility.

#### Dependencies Updated to Latest Compatible Versions

| Dependency | Previous | Latest | Notes |
|------------|----------|--------|-------|
| **Framework** |
| Temporal SDK | 1.33.0 | 1.32.1 | Latest LTS version |
| Spring Boot | 4.0.1 | 4.0.2 | Latest Spring Boot 4.0.x |
| **Observability** |
| OpenTelemetry BOM | 1.48.0 | 1.58.0 | Latest stable release |
| Micrometer Prometheus | 1.15.3 | 1.16.2 | Latest stable release |
| **Data Processing** |
| Jackson | 2.19.1 | 2.20.2 | Managed by Spring Boot 4.0.2 BOM |
| Protocol Buffers | 4.27.0 | 4.33.4 | Required for @Generated annotation support |
| Guava | 33.3.1-jre | 33.5.0-jre | Latest LTS version |
| **Logging** |
| Logback | 1.5.16 | 1.5.25 | Latest 1.5.x release |
| SLF4J | 2.0.17 | 2.0.17 | No update needed |
| **Testing** |
| JUnit Jupiter | 5.11.3 | 6.0.2 | Major version upgrade to JUnit 6 |
| Mockito | 5.14.2 | 5.21.0 | Latest stable release |
| AssertJ | 3.27.0 | 3.27.6 | Latest 3.27.x release |
| **API Documentation** |
| Swagger/OpenAPI Jakarta | 2.2.26 | 2.2.42 | Latest 2.2.x release |
| SpringDoc OpenAPI UI | 2.9.1 | 3.0.1 | Major version upgrade to 3.0 |

#### Protocol Buffer Generation Notes

**Issue**: Generated protobuf files were created with `@com.google.protobuf.Generated` annotations, but earlier versions of protobuf-java (< 4.33.4) don't include this annotation class.

**Solution**:
- Verify protobuf-java version matches the version used by buf code generator
- The generated files include a comment showing the protobuf compiler version used: `// Protobuf Java Version: X.Y.Z`
- Update pom.xml to use the matching or newer protobuf-java version
- Current version: 4.33.4 (includes the @Generated annotation)

**Regeneration**:
- Run `buf generate` from project root to regenerate Java files from .proto definitions
- This ensures consistency between generated code and runtime libraries

#### Build Command

```bash
cd /Users/mnichols/dev/temporal-oms/java
mvn clean install -DskipTests
```

All 14 modules build successfully with Java 21 bytecode target.

#### Compatibility Notes

- **Java 21**: Primary target version for all new development
- **Backward Compatibility**: Code compiles to Java 21 bytecode; consider if earlier JVM versions need support
- **Spring Boot 4.0.2**: Requires minimum Spring Framework 6.1+, compatible with Java 21
- **JUnit 6.0.2**: Major version update; ensure test code is compatible with JUnit 6 API changes
- **SpringDoc 3.0.1**: Major version update; API may differ from 2.x versions

#### Troubleshooting

If you encounter `error: invalid target release: 21` or `error: release version 21 not supported`:

1. Verify Maven is running with Java 21:
   ```bash
   mvn --version
   # Should show "Java version: 21.x.x"
   ```

2. Verify maven-compiler-plugin configuration includes:
   ```xml
   <dependency>
       <groupId>org.codehaus.plexus</groupId>
       <artifactId>plexus-compiler-javac</artifactId>
       <version>2.16.1</version>
   </dependency>
   ```

3. Clear Maven cache if needed:
   ```bash
   rm -rf ~/.m2/repository/org/apache/maven/plugins/maven-compiler-plugin
   rm -rf ~/.m2/repository/org/codehaus/plexus/plexus-compiler*
   ```

#### Verification

All modules compile successfully with Java 21:
- ✅ Generated Code (protobuf)
- ✅ Apps Core (workflows, config)
- ✅ Apps API (REST endpoints)
- ✅ Apps Workers (Temporal workers)
- ✅ Processing Core (order processing)
- ✅ Processing API (REST endpoints)
- ✅ Processing Workers (Temporal workers)
- ✅ Risk Core (fraud detection)
- ✅ Risk API (REST endpoints)
- ✅ Risk Workers (Temporal workers)

---

*Last Updated: January 24, 2026*