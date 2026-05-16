import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Meaning Before Jargon',
    description:
      'Articles begin with the idea a learner can hold, then introduce the standard physics term once it has a job to do.',
  },
  {
    title: 'Claims Kept Careful',
    description:
      'Drafts are generated with claim extraction, source checks, and review artifacts before they are promoted into the public curriculum.',
  },
  {
    title: 'A Connected Map',
    description:
      'The curriculum is organized around state, change, symmetry, conservation, fields, particles, interactions, and geometry.',
  },
];

function Feature({title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
