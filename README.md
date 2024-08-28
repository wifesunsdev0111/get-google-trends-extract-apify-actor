## Google Trending Now Scraper using Selenium & Requests & Proxies & ThreadPoolExecutor & Chrome 

Google Trending Scraper built with Selenium, Requests, Proxies, ThreadPoolExecutor and a headless Chrome browser to scrape https://trends.google.com/ website and save the results to storage. All the query params of the Scraper is passed in via input, which is defined by the [input schema](https://docs.apify.com/platform/actors/development/input-schema). This actor uses the [Selenium WebDriver](https://www.selenium.dev/documentation/webdriver/) to load and process the page. The data are then stored in the default [dataset](https://docs.apify.com/platform/storage/dataset) where you can easily access them.

## Included features

- **[Apify SDK](https://docs.apify.com/sdk/python/)** for Python - a toolkit for building Apify [Actors](https://apify.com/actors) and scrapers in Python
- **[Input schema](https://docs.apify.com/platform/actors/development/input-schema)** - define and easily validate a schema for your Actor's input
- **[Dataset](https://docs.apify.com/sdk/python/docs/concepts/storages#working-with-datasets)** - store structured data where each object stored has the same attributes
- **[Selenium](https://pypi.org/project/selenium/)** - a browser automation library
- **[Requests]** - http/https request and response library
- **[Proxies]** - Apify Datacenter proxy to bypass IP blocking
- **[ThreadPoolExecutor]** - Python library to improve the execution speed of scraper

## How it works

This code is a Python script that uses Selenium, Requests, Proxies and ThreadPoolExecutor to scrape  https://trends.google.com/ and extract data from them. Here's a brief overview of how it works:

- The script reads the input data from the Actor instance, which is expected to contain a `country` key with a list of locations to scrape, a `sort` key with a list of sort data to scrap, a `status` key with a list of trend status to scrap, `logger` key with the value that determines whether the logger outputs, a `max_items` key with the maximum number of data to scrap.
- The script creates a main request URL with the given input values ​​as parameters.
- The script uses seleniumwire webdriver to open a Chrome browser with the main URL, then parses the HTML elements to extract the trend's title, search volume, started, status, and articles.
- The script uses a URL with the main parameters of the trend's title and `country` input parameter to make an https post request to get the request parameters for the topics rising and topics top data of the explore page of https://trends.google.com/.
- The script gets all the explore topics rising and explore topics top data corresponding to the given trend using https get request based on the obtained input parameters.
- The script uses Apify Datacenter Proxy to bypass IP blocking and uses ThreadPoolExecutor to increase the execution speed.
- The script extracts the desired data from the page (title, search volume, started, status, articles, explore topics rising, explore topics top) and pushes them to the default dataset using the `push_data` method of the Actor instance.
- The script catches any exceptions that occur during the [web scraping](https://apify.com/web-scraping) process and logs an error message using the `Actor.log.exception` method.

## Resources

- [Selenium controlled Chrome example](https://apify.com/apify/example-selenium)
- [Selenium Grid: what it is and how to set it up](https://blog.apify.com/selenium-grid-what-it-is-and-how-to-set-it-up/)
- [Web scraping with Selenium and Python](https://blog.apify.com/web-scraping-with-selenium-and-python/)
- [Cypress vs. Selenium for web testing](https://blog.apify.com/cypress-vs-selenium/)
- [Python tutorials in Academy](https://docs.apify.com/academy/python)
- [Video guide on getting scraped data using Apify API](https://www.youtube.com/watch?v=ViYYDHSBAKM)
- A short guide on how to build web scrapers using code templates:

[web scraper template](https://www.youtube.com/watch?v=u-i-Korzf8w)


## Getting started

For complete information [see this article](https://docs.apify.com/platform/actors/development#build-actor-locally). To run the actor use the following command:

```bash
apify run
```

## Deploy to Apify

### Connect Git repository to Apify

If you've created a Git repository for the project, you can easily connect to Apify:

1. Go to [Actor creation page](https://console.apify.com/actors/new)
2. Click on **Link Git Repository** button

### Push project on your local machine to Apify

You can also deploy the project on your local machine to Apify without the need for the Git repository.

1. Log in to Apify. You will need to provide your [Apify API Token](https://console.apify.com/account/integrations) to complete this action.

    ```bash
    apify login
    ```

2. Deploy your Actor. This command will deploy and build the Actor on the Apify Platform. You can find your newly created Actor under [Actors -> My Actors](https://console.apify.com/actors?tab=my).

    ```bash
    apify push
    ```

## Documentation reference

To learn more about Apify and Actors, take a look at the following resources:

- [Apify SDK for JavaScript documentation](https://docs.apify.com/sdk/js)
- [Apify SDK for Python documentation](https://docs.apify.com/sdk/python)
- [Apify Platform documentation](https://docs.apify.com/platform)
- [Join our developer community on Discord](https://discord.com/invite/jyEM2PRvMU)
