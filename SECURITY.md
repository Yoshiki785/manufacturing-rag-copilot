# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to the repository maintainers
3. Include detailed steps to reproduce the vulnerability
4. Allow reasonable time for a fix before public disclosure

## Security Best Practices

### For Operators

- Never commit `.env` files or API keys
- Use secrets management in production
- Enable audit logging
- Regularly rotate API keys
- Keep dependencies updated

### For Contributors

- Never log sensitive data
- Validate all user inputs
- Use parameterized database queries
- Follow secure coding guidelines

## Known Security Considerations

- OpenAI API keys must be kept confidential
- Database credentials should use least-privilege access
- User-uploaded documents should be scanned for malware
- Rate limiting should be enabled in production
