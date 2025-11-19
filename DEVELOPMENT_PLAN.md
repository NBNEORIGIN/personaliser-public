# NBNE Personaliser - Development Plan

## Project Status: Moonshot 🚀

**Goal**: Transform working demo into production-ready SaaS platform for personalized product manufacturers.

---

## Branch Strategy

### `main` - Stable Demo (Protected)
- **Purpose**: Beta testing and demonstrations
- **Deployment**: https://demo.nbne.uk
- **Changes**: Bug fixes only, no new features
- **Protection**: Require PR reviews before merge

### `development` - Active Development
- **Purpose**: New features and improvements
- **Deployment**: https://dev.nbne.uk (staging)
- **Changes**: All new development work
- **Merge to main**: Only after thorough testing

### Feature Branches
- `feature/security-hardening`
- `feature/amazon-integration`
- `feature/etsy-integration`
- `feature/ebay-integration`
- `feature/shopify-integration`
- `feature/jig-marketplace`
- `feature/font-library`
- `feature/multi-tenancy`

---

## Development Roadmap

### Phase 1: Foundation (Months 1-2)
**Goal**: Production-ready infrastructure

#### Security Hardening
- [ ] Implement proper authentication (Auth0 or Clerk)
- [ ] Add rate limiting (10 req/min per user)
- [ ] Input sanitization and validation
- [ ] Path traversal protection
- [ ] HTTPS enforcement
- [ ] API key management for integrations
- [ ] Audit logging

#### Infrastructure
- [ ] PostgreSQL database migration
- [ ] Redis caching layer
- [ ] S3/CloudFront for assets
- [ ] Background job queue (Celery/BullMQ)
- [ ] Error tracking (Sentry)
- [ ] Monitoring (Datadog/New Relic)
- [ ] CI/CD pipeline (GitHub Actions)

#### Multi-tenancy
- [ ] User registration and onboarding
- [ ] Workspace/organization model
- [ ] Usage tracking and quotas
- [ ] Billing integration (Stripe)
- [ ] Admin dashboard

### Phase 2: Platform Integrations (Months 2-4)
**Goal**: Automated order ingestion from major platforms

#### Amazon Integration
- [ ] MWS/SP-API authentication
- [ ] Real-time order webhook
- [ ] Customization data extraction
- [ ] Photo download from S3
- [ ] Order status sync
- [ ] Automated fulfillment updates

#### Etsy Integration
- [ ] OAuth 2.0 authentication
- [ ] Order webhook listener
- [ ] Personalization field mapping
- [ ] Digital file downloads
- [ ] Shipping notification sync

#### eBay Integration
- [ ] Trading API authentication
- [ ] Order polling/webhook
- [ ] Item specifics parsing
- [ ] Buyer message extraction

#### Shopify Integration
- [ ] App installation flow
- [ ] Order webhook
- [ ] Metafield extraction
- [ ] Fulfillment API integration

### Phase 3: Maker Marketplace (Months 4-6)
**Goal**: Monetize through jig and parts sales

#### Jig Configurator
- [ ] Bed size input (width, height, keepout zones)
- [ ] Material selection (acrylic, aluminum, wood)
- [ ] Pricing calculator
- [ ] 3D preview (Three.js)
- [ ] CAD file generation (DXF/SVG export)
- [ ] Order management

#### Parts Catalog
- [ ] Product database (fixtures, clamps, spacers)
- [ ] Inventory management
- [ ] Shopping cart
- [ ] Payment processing
- [ ] Shipping integration
- [ ] Supplier dropshipping

#### Community Features
- [ ] User-submitted jig designs
- [ ] Rating and reviews
- [ ] Design marketplace (commission model)
- [ ] Forum/discussion board

### Phase 4: Advanced Features (Months 6-9)
**Goal**: Differentiation and competitive advantage

#### Font Library
- [ ] Google Fonts integration
- [ ] Custom font upload
- [ ] Font preview in templates
- [ ] License compliance tracking
- [ ] Font pairing suggestions

#### Template Marketplace
- [ ] Template designer UI
- [ ] Template sharing/selling
- [ ] Version control
- [ ] Preview gallery
- [ ] Revenue sharing (70/30 split)

#### AI Features
- [ ] Auto-layout optimization
- [ ] Text fitting and scaling
- [ ] Image enhancement
- [ ] Design suggestions
- [ ] Batch processing optimization

#### Analytics
- [ ] Production efficiency metrics
- [ ] Material waste tracking
- [ ] Order volume forecasting
- [ ] Revenue analytics
- [ ] Customer insights

---

## Beta Testing Program

### Target Audience
**5 Beta Testers** - Small to medium memorial/personalization businesses

#### Ideal Profile
- 10-100 orders/month
- Using UV printer or engraver
- Currently doing manual layout
- Willing to provide feedback
- Tech-savvy enough to troubleshoot

### Beta Offer
**Lifetime Discount**: 50% off monthly subscription forever
- Normal: $99/month → Beta: $49.50/month
- Or: $999/year → Beta: $499.50/year

### Beta Duration
**3 Months** (with option to extend)

#### Month 1: Onboarding
- Setup assistance
- Training sessions
- Template creation help
- Daily check-ins

#### Month 2: Active Use
- Process real orders
- Weekly feedback calls
- Feature requests
- Bug reporting

#### Month 3: Optimization
- Workflow refinement
- Performance tuning
- Case study creation
- Testimonial collection

### Success Metrics
- [ ] 80% of orders processed through system
- [ ] <5% error rate
- [ ] 30%+ time savings vs manual
- [ ] 4+ star satisfaction rating
- [ ] Willing to provide testimonial

---

## Current Demo Assessment for Beta

### ✅ Ready for Beta
1. **Core Functionality Works**
   - Amazon TSV ingestion ✓
   - SVG/PDF generation ✓
   - Bed optimization ✓
   - Photo processing ✓
   - Template system ✓

2. **Deterministic Output**
   - Reproducible layouts ✓
   - Consistent quality ✓

3. **Basic UI**
   - File upload ✓
   - Preview generation ✓
   - Download artifacts ✓

### ⚠️ Needs Improvement Before Beta

#### Critical (Must Fix)
1. **Security**
   - [ ] Remove `BYPASS_AUTH_FOR_TESTS = True` in production
   - [ ] Add proper user authentication
   - [ ] Implement API rate limiting
   - [ ] Sanitize file uploads

2. **Stability**
   - [ ] Add error recovery for failed downloads
   - [ ] Handle edge cases (empty orders, malformed data)
   - [ ] Add request timeout handling
   - [ ] Implement retry logic

3. **Documentation**
   - [ ] User guide with screenshots
   - [ ] Video tutorials (5-10 min each)
   - [ ] FAQ section
   - [ ] Troubleshooting guide
   - [ ] API documentation

4. **Support Infrastructure**
   - [ ] Bug reporting system (GitHub Issues or Intercom)
   - [ ] Email support (support@nbne.uk)
   - [ ] Status page (status.nbne.uk)
   - [ ] Feedback form

#### Important (Should Fix)
1. **User Experience**
   - [ ] Better error messages
   - [ ] Loading states and progress bars
   - [ ] Success/failure notifications
   - [ ] Keyboard shortcuts
   - [ ] Batch operation status

2. **Data Management**
   - [ ] Job history (last 30 days)
   - [ ] Template library
   - [ ] Saved configurations
   - [ ] Export/import settings

3. **Monitoring**
   - [ ] Uptime monitoring
   - [ ] Error tracking
   - [ ] Usage analytics
   - [ ] Performance metrics

#### Nice to Have
1. **Onboarding**
   - [ ] Welcome wizard
   - [ ] Sample data
   - [ ] Interactive tutorial
   - [ ] Tooltips and hints

2. **Collaboration**
   - [ ] Share templates
   - [ ] Team workspaces
   - [ ] Comments/notes

---

## Minimum Viable Beta (2-Week Sprint)

To get demo beta-ready quickly:

### Week 1: Security & Stability
- [ ] Add simple auth (email/password)
- [ ] Rate limiting middleware
- [ ] Error boundaries in frontend
- [ ] Comprehensive error logging
- [ ] Health check monitoring

### Week 2: Documentation & Support
- [ ] Quick start guide (PDF + video)
- [ ] Template creation tutorial
- [ ] Common issues FAQ
- [ ] Support email setup
- [ ] Feedback form

### Launch Checklist
- [ ] Deploy to stable domain
- [ ] Set up monitoring alerts
- [ ] Create onboarding email sequence
- [ ] Prepare welcome packet
- [ ] Schedule kick-off calls

---

## Revenue Model (Future)

### Subscription Tiers

#### Starter - $49/month
- 500 items/month
- 2 users
- Email support
- Basic templates

#### Professional - $99/month
- 2,000 items/month
- 5 users
- Priority support
- Custom templates
- API access

#### Enterprise - $299/month
- Unlimited items
- Unlimited users
- Dedicated support
- White-label option
- Custom integrations

### Additional Revenue Streams
1. **Jig Sales**: 30% margin on custom jigs ($200-500 each)
2. **Template Marketplace**: 30% commission on sales
3. **Professional Services**: $150/hr for custom development
4. **Training**: $500 for onboarding package

---

## Risk Mitigation

### Technical Risks
- **Downtime**: Multi-region deployment, 99.9% SLA
- **Data Loss**: Daily backups, point-in-time recovery
- **Security Breach**: Penetration testing, bug bounty program
- **Scalability**: Auto-scaling infrastructure, load testing

### Business Risks
- **Low Adoption**: Free tier to reduce barrier to entry
- **Competition**: Focus on niche (memorial products)
- **Customer Churn**: Excellent support, continuous improvement
- **Platform Changes**: Diversify integrations, own customer data

---

## Next Steps

1. **Immediate** (This Week)
   - Create `development` branch
   - Set up staging environment
   - Document current system
   - List beta tester requirements

2. **Short-term** (Next 2 Weeks)
   - Implement critical security fixes
   - Create user documentation
   - Set up support infrastructure
   - Recruit beta testers

3. **Medium-term** (Next 3 Months)
   - Run beta program
   - Iterate based on feedback
   - Build Phase 1 features
   - Prepare for public launch

---

## Success Criteria

### Beta Success
- 4/5 testers complete full 3 months
- Average 4+ star rating
- 2+ willing to be case studies
- <10 critical bugs found
- 50%+ time savings demonstrated

### Product-Market Fit
- 50+ paying customers within 6 months
- $5,000+ MRR
- <10% monthly churn
- Net Promoter Score >40
- 80%+ feature adoption

### Moonshot Success (2-Year Goal)
- 500+ customers
- $50,000+ MRR
- Team of 5-10 people
- Market leader in niche
- Acquisition interest or sustainable growth

---

## Questions to Answer

1. **Pricing**: Is $99/month the right price point?
2. **Target Market**: Memorial only or broader personalization?
3. **Geography**: UK-focused or international?
4. **Support Model**: Self-service or high-touch?
5. **Partnership**: Integrate with printer manufacturers?

---

**Last Updated**: 2025-11-19
**Owner**: NBNE Team
**Status**: Planning Phase
