const products = {}
var info = {}
const category = () => document.getElementById('category').value

const loadData = async () => {
    let response = await fetch('info.json')
    let data = await response.json()

    info = data
    addCategories(info.categories)
}
const addCategories = categories => {
    const elem = document.getElementById('category')
    for (key in Object.keys(categories)) {
        if (categories[key] === undefined)
            continue

        const option = document.createElement('option')
        option.value = key
        option.text = categories[key]
        elem.appendChild(option)
    }
}

const compareStores = async () => {
    storeStock = await getStoreStock([
        document.getElementById('store1').value,
        document.getElementById('store2').value
    ])

    const category = document.getElementById('category').value
    await getProductsByCategory(category)

    const diff = getStockDiff(storeStock, category)

    const products = getProductInformation(diff, category)
    viewProductDiff(products)
}

const getStores = async () => {
    var selects = [document.getElementById('store1'), document.getElementById('store2')]

    let response = await fetch('stores/info.json')
    let data = await response.json()

    data.forEach(store => {
        const [nr, name, city] = store

        selects.forEach(select => {
            const option = document.createElement('option')
            option.value = nr
            option.text = `${city} - ${name}`
            select.appendChild(option)
        })
    })
}

const addEventListener = () => {
    document.getElementById('compare')
        .addEventListener('click', compareStores)
    document.getElementById('compare-form')
        .addEventListener('submit', e => e.preventDefault())
}

const _getStoreStock = async (nr) => {
    let response = await fetch(`stores/${nr}.json`)
    let data = await response.json()
    return data
}
const getStoreStock = async (storeNr) => {
    let promises = storeNr.map(store => _getStoreStock(store))

    let results = []
    for (let promise of promises) {
        results.push(await promise)
    }
    return results
}

var storeDiffStock = []

const getProductInformation = (ids, category) => {
    return ids.map(diff =>
        diff.map(id => products[category][id])
    )
}

const getProductsByCategory = async (category) => {
    if (products[category])
        return

    let response = await fetch(`products/${category}.json`)
    let data = await response.json()
    products[category] = data
}

const viewProductDiff = stores => {
    const store1 = document.getElementById('store1Result')
    const store2 = document.getElementById('store2Result')

    while (store1.hasChildNodes())
        store1.removeChild(store1.lastChild)

    while (store2.hasChildNodes())
        store2.removeChild(store2.lastChild)

    stores[0].forEach(product => addProduct(product, store1))
    stores[1].forEach(product => addProduct(product, store2))
}

const addProduct = (product, elem) => {
    const p = document.createElement('div')
    p.classList.add('col-sm-4')

    const p2 = document.createElement('div')
    p2.classList.add('product')

    const [name, name2, price, url, country, format, volume, style, type] = product

    const link = document.createElement('a')
    link.href = `https://systembolaget.se/dryck/${url}`

    const pName = document.createElement('div')
    pName.classList.add('product-name')
    pName.innerText += name

    const pText = document.createElement('div')
    pText.classList.add('product-text')
    pText.innerHTML += country && `${info.countries[country]}<br />`
    pText.innerHTML += style && `${info.styles[style]}<br />`
    pText.innerHTML += type && `${info.types[type]}`

    link.appendChild(pName)
    link.appendChild(pText)

    p2.appendChild(link)
    p.appendChild(p2)

    elem.appendChild(p)
}

const getStockDiff = (stock, category) => {
    const categories = stock.map(x => x[category])
    const diff = categories.map((c, i, t) => {
        const flat = t.filter(y => y !== c).reduce((a, z) => a.concat(z), [])
        return c.filter(n => flat.filter(g => g === n).length < t.length - 1)
    })
    return diff
}

addEventListener()
loadData()
getStores()